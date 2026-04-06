def endpoint(response: Annotated[Response, Depends(second_modifier)]):
        return {"status": "ok"}