def _blob_to_data_url(blob, mime_type="image/png"):
        if isinstance(blob, str):
            blob = blob.strip()
            if blob.startswith("data:") or blob.startswith("http://") or blob.startswith("https://") or blob.startswith("file://"):
                return blob
            return f"data:{mime_type};base64,{blob}"
        if isinstance(blob, BytesIO):
            blob = blob.getvalue()
        if isinstance(blob, memoryview):
            blob = blob.tobytes()
        if isinstance(blob, bytearray):
            blob = bytes(blob)
        if isinstance(blob, bytes):
            b64 = base64.b64encode(blob).decode("utf-8")
            return f"data:{mime_type};base64,{b64}"
        return None