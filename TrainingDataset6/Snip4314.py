async def send(message: dict) -> None:  # type: ignore[type-arg]
        if message["type"] == "http.response.body":
            chunks.append(message.get("body", b""))