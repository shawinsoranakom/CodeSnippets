def as_json(self, escape_html=False):
        return json.dumps(self.get_json_data(escape_html))