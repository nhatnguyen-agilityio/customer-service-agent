import requests
import sqlalchemy.exc
from postgrest.exceptions import APIError

from langchain.messages import ToolMessage


def handle_tool_errors(request, handler):
    try:
        return handler(request)
    except requests.exceptions.Timeout:
        content = "This request took too long to complete. Please try again in a moment."
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response is not None else None
        if status == 429:
            content = "We're receiving too many requests right now. Please try again shortly."
        elif status in (401, 403):
            content = "There was an authentication issue reaching an external service. Please contact support."
        else:
            content = "An external service returned an error. Please try again."
    except APIError as e:
        if e.code == 401:
            content = "There was an authentication issue accessing the database. Please contact support."
        else:
            content = "There was a problem accessing the database. Please try again."
    except sqlalchemy.exc.OperationalError:
        content = "We're having trouble connecting to the database right now. Please try again in a moment."
    except Exception:
        content = "Something went wrong while processing your request. Please try again, or rephrase your question."

    return ToolMessage(
        content=content,
        tool_call_id=request.tool_call.get("id", ""),
    )
