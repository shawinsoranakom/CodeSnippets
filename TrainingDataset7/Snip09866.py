def adapt_json_value(self, value, encoder):
        return Jsonb(value, dumps=get_json_dumps(encoder))