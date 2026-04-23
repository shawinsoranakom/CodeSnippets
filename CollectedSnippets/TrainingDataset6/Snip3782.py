def extract_request_info(request: Request) -> dict:
        return {
            "path": request.url.path,
            "user_agent": request.headers.get("user-agent", "unknown"),
        }