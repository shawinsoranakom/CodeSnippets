def _encode_special_floats(cls, obj: Any) -> Any:
        """
        Iterates over the passed object and encode specific floats that cannot be JSON-serialized. Python's JSON
        engine saves floats like `Infinity` (+/-) or `NaN` which are not compatible with other JSON engines.

        It serializes floats like `Infinity` as an object: `{'__float__': Infinity}`.
        """
        if isinstance(obj, float):
            if math.isnan(obj):
                return {_FLOAT_TAG_KEY: "NaN"}
            if obj == float("inf"):
                return {_FLOAT_TAG_KEY: "Infinity"}
            if obj == float("-inf"):
                return {_FLOAT_TAG_KEY: "-Infinity"}
            return obj

        if isinstance(obj, dict):
            return {k: cls._encode_special_floats(v) for k, v in obj.items()}

        if isinstance(obj, (list, tuple)):
            return [cls._encode_special_floats(v) for v in obj]

        return obj