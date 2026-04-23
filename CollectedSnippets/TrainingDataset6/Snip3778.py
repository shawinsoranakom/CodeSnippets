def second_modifier(
        response: Annotated[Response, Depends(first_modifier)],
    ) -> Response:
        response.headers["X-Second"] = "2"
        return response