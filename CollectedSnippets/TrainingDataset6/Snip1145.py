def generate_stream(query: str):
    for ch in query:
        yield ch
        time.sleep(0.1)