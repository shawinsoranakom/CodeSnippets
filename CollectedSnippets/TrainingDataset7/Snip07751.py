def prepare_value(self, value):
        if isinstance(value, dict):
            return json.dumps(value, ensure_ascii=False)
        return value