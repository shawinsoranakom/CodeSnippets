def image2base64(image):
        # Return a data URL with the correct MIME to avoid provider mismatches
        if isinstance(image, bytes):
            # Best-effort magic number sniffing
            mime = "image/png"
            if len(image) >= 2 and image[0] == 0xFF and image[1] == 0xD8:
                mime = "image/jpeg"
            b64 = base64.b64encode(image).decode("utf-8")
            return f"data:{mime};base64,{b64}"
        if isinstance(image, BytesIO):
            data = image.getvalue()
            mime = "image/png"
            if len(data) >= 2 and data[0] == 0xFF and data[1] == 0xD8:
                mime = "image/jpeg"
            b64 = base64.b64encode(data).decode("utf-8")
            return f"data:{mime};base64,{b64}"
        with BytesIO() as buffered:
            fmt = "jpeg"
            try:
                image.save(buffered, format="JPEG")
            except Exception:
                # reset buffer before saving PNG
                buffered.seek(0)
                buffered.truncate()
                image.save(buffered, format="PNG")
                fmt = "png"
            data = buffered.getvalue()
            b64 = base64.b64encode(data).decode("utf-8")
            mime = f"image/{fmt}"
        return f"data:{mime};base64,{b64}"