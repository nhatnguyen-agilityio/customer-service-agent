-- Run this in the Supabase SQL editor (Project -> SQL Editor -> New query).
-- ---------------------------------------------------------------------------
-- Retail data: products, customers, orders, order_items
-- ---------------------------------------------------------------------------

create table products (
    id bigserial primary key,
    name text not null,
    category text not null,
    description text,
    price numeric(10, 2) not null,
    stock_qty integer not null default 0
);

create table customers (
    id bigserial primary key,
    email text not null unique,
    name text not null
);

create table orders (
    id bigserial primary key,
    customer_id bigint not null references customers(id),
    status text not null default 'processing',
    created_at timestamptz not null default now(),
    total numeric(10, 2) not null,
    estimated_delivery timestamptz
);
create index orders_customer_id_idx on orders(customer_id);

create table order_items (
    order_id bigint not null references orders(id),
    product_id bigint not null references products(id),
    quantity integer not null,
    unit_price numeric(10, 2) not null,
    primary key (order_id, product_id)
);
create index order_items_order_id_idx on order_items(order_id);
create index order_items_product_id_idx on order_items(product_id);

-- ---------------------------------------------------------------------------
-- FAQ RAG: pgvector + the exact `documents` table shape and `match_documents`
-- RPC signature that langchain_community.vectorstores.SupabaseVectorStore
-- expects -- verified against the installed library source, not assumed:
--   - insert writes only {content, embedding, metadata, [id]} (SupabaseVectorStore._add_vectors)
--   - the RPC is called with ONLY {query_embedding, [filter]} -- match_count is
--     NEVER passed, so match_documents must not require it; the `k` limit is
--     applied by PostgREST's .limit() on the RPC call, not inside the function.
-- Embedding dimension is 1536 to match OpenAI's text-embedding-3-small,
-- the same model used in country-travel-assistant.py.
-- ---------------------------------------------------------------------------

create extension if not exists vector;

create table documents (
    id bigserial primary key,
    content text,
    metadata jsonb,
    embedding vector(1536)
);

-- Optional but recommended once there's more than a handful of FAQ rows --
-- speeds up similarity search. Cheap to add now even at small scale.
create index documents_embedding_idx on documents
    using hnsw (embedding vector_cosine_ops);

create function match_documents (
    query_embedding vector(1536),
    filter jsonb DEFAULT '{}'
) returns table (
    id bigint,
    content text,
    metadata jsonb,
    similarity float
)
language plpgsql
as $$
begin
    return query
    select
        documents.id,
        documents.content,
        documents.metadata,
        1 - (documents.embedding <=> query_embedding) as similarity
    from documents
    where documents.metadata @> filter
    order by documents.embedding <=> query_embedding;
end;
$$;


create role agent_readonly with login password '<set a real password>';
grant connect on database postgres to agent_readonly;
grant usage on schema public to agent_readonly;
grant select on all tables in schema public to agent_readonly;
alter default privileges in schema public grant select on tables to agent_readonly;

create policy agent_readonly_select on products for select to agent_readonly using (true);
create policy agent_readonly_select on customers for select to agent_readonly using (true);
create policy agent_readonly_select on orders for select to agent_readonly using (true);
create policy agent_readonly_select on order_items for select to agent_readonly using (true);

-- ---------------------------------------------------------------------------
-- Rate limiting -- one row per customer, tracking a rolling message-count
-- window. See src/security/rate_limit.py.
-- ---------------------------------------------------------------------------

create table rate_limits (
    customer_email text primary key,
    window_start timestamptz not null,
    message_count integer not null default 0
);
