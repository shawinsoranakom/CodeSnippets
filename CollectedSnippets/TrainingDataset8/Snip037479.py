def _BytesIO_to_bytes(data: io.BytesIO) -> bytes:
    data.seek(0)
    return data.getvalue()