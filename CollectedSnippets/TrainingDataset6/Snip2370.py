async def middleware(request, call_next):
    response: StreamingResponse = await call_next(request)
    response.headers["x-state"] = json.dumps(state.copy())
    return response