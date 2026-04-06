def default_response() -> Response:
        response = JSONResponse(content={"status": "ok"})
        response.headers["X-Custom"] = "initial"
        return response