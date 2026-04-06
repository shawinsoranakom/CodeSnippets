async def query_model(data: Model = Query()):
    return {"param": data.param}