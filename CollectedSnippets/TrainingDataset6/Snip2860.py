async def patched_read(self: StarletteUploadFile, size: int = -1) -> bytes:
        # Make the FIRST file slower *deterministically*
        if self.filename == "slow.txt":
            await anyio.sleep(0.05)
        return await original_read(self, size)