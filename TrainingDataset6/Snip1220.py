def get_data() -> DataOutput:
    data = "hello".encode("utf-8")
    return DataOutput(description="A plumbus", data=data)