def endpoint(response: Annotated[Response, Depends(modify_response)]):
        return {"status": "ok"}