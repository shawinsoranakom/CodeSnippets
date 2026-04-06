def generate(query: str):
    return StreamingResponse(content=generate_stream(query))