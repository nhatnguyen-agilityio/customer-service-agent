import os
import sys

import psycopg
from dotenv import load_dotenv

load_dotenv()

RETENTION_INTERVAL = os.environ.get("CHECKPOINT_RETENTION_INTERVAL", "3 days")


def prune(conn: psycopg.Connection, dry_run: bool) -> None:
    print(f"Retention interval: {RETENTION_INTERVAL!r}")
    cur = conn.cursor()
    try:
        cur.execute(
            """
            CREATE TEMP TABLE old_checkpoints ON COMMIT DROP AS
            SELECT thread_id, checkpoint_ns, checkpoint_id
            FROM checkpoints
            WHERE (checkpoint->>'ts')::timestamptz < now() - (%s)::interval
            """,
            (RETENTION_INTERVAL,),
        )

        cur.execute(
            """
            CREATE TEMP TABLE keep_refs ON COMMIT DROP AS
            SELECT thread_id, checkpoint_ns, kv.key AS channel, kv.value AS version
            FROM checkpoints, jsonb_each_text(checkpoint->'channel_versions') AS kv
            WHERE (checkpoint->>'ts')::timestamptz >= now() - (%s)::interval
            """,
            (RETENTION_INTERVAL,),
        )

        cur.execute("SELECT count(*) FROM old_checkpoints")
        old_checkpoint_count = cur.fetchone()[0]

        cur.execute(
            """
            SELECT count(*)
            FROM checkpoint_writes cw
            JOIN old_checkpoints oc
              ON cw.thread_id = oc.thread_id
             AND cw.checkpoint_ns = oc.checkpoint_ns
             AND cw.checkpoint_id = oc.checkpoint_id
            """
        )
        old_writes_count = cur.fetchone()[0]

        cur.execute(
            """
            SELECT count(*)
            FROM checkpoint_blobs cb
            WHERE NOT EXISTS (
                SELECT 1 FROM keep_refs kr
                WHERE kr.thread_id = cb.thread_id
                  AND kr.checkpoint_ns = cb.checkpoint_ns
                  AND kr.channel = cb.channel
                  AND kr.version = cb.version
            )
            """
        )
        old_blobs_count = cur.fetchone()[0]

        print(f"Would delete: {old_checkpoint_count} checkpoints, {old_writes_count} writes, {old_blobs_count} blobs")

        if dry_run:
            print("Dry run -- rolling back, nothing deleted.")
            conn.rollback()
            return

        cur.execute(
            """
            DELETE FROM checkpoint_writes cw
            USING old_checkpoints oc
            WHERE cw.thread_id = oc.thread_id
              AND cw.checkpoint_ns = oc.checkpoint_ns
              AND cw.checkpoint_id = oc.checkpoint_id
            """
        )

        cur.execute(
            """
            DELETE FROM checkpoints c
            USING old_checkpoints oc
            WHERE c.thread_id = oc.thread_id
              AND c.checkpoint_ns = oc.checkpoint_ns
              AND c.checkpoint_id = oc.checkpoint_id
            """
        )

        cur.execute(
            """
            DELETE FROM checkpoint_blobs cb
            WHERE NOT EXISTS (
                SELECT 1 FROM keep_refs kr
                WHERE kr.thread_id = cb.thread_id
                  AND kr.checkpoint_ns = cb.checkpoint_ns
                  AND kr.channel = cb.channel
                  AND kr.version = cb.version
            )
            """
        )

        conn.commit()
        print(f"Deleted {old_checkpoint_count} checkpoints, {old_writes_count} writes, {old_blobs_count} blobs.")
    finally:
        cur.close()


if __name__ == "__main__":
    dry_run = "--apply" not in sys.argv
    conn = psycopg.connect(os.environ["SUPABASE_DB_URL"], autocommit=False)
    prune(conn, dry_run=dry_run)
    conn.close()
