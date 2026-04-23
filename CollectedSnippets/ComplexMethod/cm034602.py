def _findKey(self, json: Any, key: str) -> Union[str, None]:  # TODO: Fix json type
        """Recursively search for a key in nested dictionary/list structures."""
        if isinstance(json, list):
            for elm in json:
                ret = self._findKey(elm, key)
                if ret is not None:
                    return ret
        elif isinstance(json, dict):
            for k, v in json.items():
                if k == key:
                    return json[k]
                if result := self._findKey(v, key):
                    return result
        return None