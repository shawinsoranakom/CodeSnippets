def get_prep_value(self, value):
            return json.dumps(value, cls=self.encoder)