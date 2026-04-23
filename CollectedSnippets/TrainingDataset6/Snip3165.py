async def cookie_model(data: Model = Cookie()):
    return {"param": data.param}