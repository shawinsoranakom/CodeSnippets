async def header_model(data: Model = Header()):
    return {"param": data.param}