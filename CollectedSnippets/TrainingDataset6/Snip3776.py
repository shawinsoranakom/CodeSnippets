def endpoint(response: Response):
        response.headers["X-Direct"] = "set"
        return {"status": "ok"}