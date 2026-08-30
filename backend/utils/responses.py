from typing import Any, Optional
from fastapi.responses import JSONResponse


_UNSET = object()


def success_response(
    data: Any = _UNSET,
    message: Optional[str] = None,
    status_code: int = 200
) -> JSONResponse:
    """
    Constructs a standard success response according to API contracts.
    """
    content = {
        "success": True,
        "data": {} if data is _UNSET else data
    }
    if message is not None:
        content["message"] = message

    return JSONResponse(status_code=status_code, content=content)


def error_response(
    code: str,
    message: str,
    status_code: int = 400
) -> JSONResponse:
    """
    Constructs a standard error response according to API contracts.
    """
    content = {
        "success": False,
        "error": {
            "code": code,
            "message": message
        }
    }
    return JSONResponse(status_code=status_code, content=content)
