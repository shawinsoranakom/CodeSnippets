def _copy_service_dict(self, service_dict: dict) -> dict:
        if not isinstance(service_dict, dict):
            return service_dict
        result = {}
        for key, value in service_dict.items():
            if isinstance(value, dict):
                result[key] = self._copy_service_dict(value)
            elif isinstance(value, bytes) and len(value) > self.bytes_length_display_threshold:
                result[key] = f"Bytes({format_bytes(len(value))})"
            elif isinstance(value, list):
                result[key] = [self._copy_service_dict(item) for item in value]
            else:
                result[key] = value
        return result