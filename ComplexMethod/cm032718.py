def _normalize_image(self, image):
        if isinstance(image, dict):
            inline_data = image.get("inline_data")
            if isinstance(inline_data, dict):
                mime = inline_data.get("mime_type") or "image/png"
                data_url = self._blob_to_data_url(inline_data.get("data"), mime)
                if data_url:
                    return data_url

            image_url = image.get("image_url")
            if isinstance(image_url, dict):
                data_url = self._blob_to_data_url(image_url.get("url"), image.get("mime_type") or "image/png")
                if data_url:
                    return data_url
            if isinstance(image_url, str):
                data_url = self._blob_to_data_url(image_url, image.get("mime_type") or "image/png")
                if data_url:
                    return data_url

            if "url" in image:
                data_url = self._blob_to_data_url(image.get("url"), image.get("mime_type") or "image/png")
                if data_url:
                    return data_url

            mime = image.get("mime_type") or image.get("media_type") or "image/png"
            for key in ("blob", "data"):
                if key in image:
                    data_url = self._blob_to_data_url(image.get(key), mime)
                    if data_url:
                        return data_url

        if isinstance(image, (bytes, bytearray, memoryview, BytesIO)):
            return self.image2base64(image)
        if isinstance(image, str):
            return self._blob_to_data_url(image, "image/png")
        return self.image2base64(image)