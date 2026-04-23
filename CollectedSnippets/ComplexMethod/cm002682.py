def _decode_special_floats(cls, obj: Any) -> Any:
        """
        Iterates over the passed object and decode specific floats that cannot be JSON-serialized. Python's JSON
        engine saves floats like `Infinity` (+/-) or `NaN` which are not compatible with other JSON engines.

        This method deserializes objects like `{'__float__': Infinity}` to their float values like `Infinity`.
        """
        if isinstance(obj, dict):
            if set(obj.keys()) == {_FLOAT_TAG_KEY} and isinstance(obj[_FLOAT_TAG_KEY], str):
                tag = obj[_FLOAT_TAG_KEY]
                if tag in _FLOAT_TAG_VALUES:
                    return _FLOAT_TAG_VALUES[tag]
                return obj

            return {k: cls._decode_special_floats(v) for k, v in obj.items()}

        if isinstance(obj, list):
            return [cls._decode_special_floats(v) for v in obj]

        return obj