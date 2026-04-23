async def run(self, input_data: Input, **kwargs) -> BlockOutput:
        obj = input_data.input
        key = input_data.key

        if isinstance(obj, str):
            obj = loads(obj)

        if isinstance(obj, dict) and key in obj:
            yield "output", obj[key]
        elif isinstance(obj, list) and isinstance(key, int) and 0 <= key < len(obj):
            yield "output", obj[key]
        elif isinstance(obj, list) and isinstance(key, str):
            if len(obj) == 0:
                yield "output", []
            elif isinstance(obj[0], dict) and key in obj[0]:
                yield "output", [item[key] for item in obj if key in item]
            else:
                yield "output", [getattr(val, key) for val in obj if hasattr(val, key)]
        elif isinstance(obj, object) and isinstance(key, str) and hasattr(obj, key):
            yield "output", getattr(obj, key)
        else:
            yield "missing", input_data.input