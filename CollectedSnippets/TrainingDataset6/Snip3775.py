def endpoint(response: Response = Depends(modify_response)):
        return {"status": "ok"}