async def upload(files: Annotated[list[bytes], File()]):
        # return something that makes order obvious
        return [b[0] for b in files]