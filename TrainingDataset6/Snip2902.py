async def create_message(input_message: str) -> Message:
    return Message(
        input=input_message,
        output=MessageOutput(body=f"Processed: {input_message}"),
    )