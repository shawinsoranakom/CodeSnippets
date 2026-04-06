def modify_response(response: Response) -> Response:
        response.headers["X-Custom"] = "modified"
        return response