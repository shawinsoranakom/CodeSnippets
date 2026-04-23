def _remove_data_images(cls, value):
        if value is None:
            return None

        if isinstance(value, str):
            return None if value.strip().startswith("data:image/") else value

        if isinstance(value, list):
            cleaned = []
            for item in value:
                v = cls._remove_data_images(item)
                if v is None:
                    continue
                if isinstance(v, (list, tuple, set, dict)) and not v:
                    continue
                cleaned.append(v)
            return cleaned

        if isinstance(value, tuple):
            cleaned = []
            for item in value:
                v = cls._remove_data_images(item)
                if v is None:
                    continue
                if isinstance(v, (list, tuple, set, dict)) and not v:
                    continue
                cleaned.append(v)
            return tuple(cleaned)

        if isinstance(value, set):
            cleaned = []
            for item in value:
                v = cls._remove_data_images(item)
                if v is None:
                    continue
                if isinstance(v, (list, tuple, set, dict)) and not v:
                    continue
                cleaned.append(v)
            return cleaned

        if isinstance(value, dict):
            if value.get("type") in {"image_url", "input_image", "image"} and cls._extract_data_images(value):
                return None

            cleaned = {}
            for k, item in value.items():
                v = cls._remove_data_images(item)
                if v is None:
                    continue
                if isinstance(v, (list, tuple, set, dict)) and not v:
                    continue
                cleaned[k] = v
            return cleaned

        return value