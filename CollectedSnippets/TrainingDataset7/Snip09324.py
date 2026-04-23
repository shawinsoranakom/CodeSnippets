def adapt_json_value(self, value, encoder):
        return json.dumps(value, cls=encoder)