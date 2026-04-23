def endpoint(response: Annotated[Response, Depends(default_response)]):
        response.headers["X-Custom"] = "modified"
        return response