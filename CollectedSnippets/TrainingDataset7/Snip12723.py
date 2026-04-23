def get_json_data(self, escape_html=False):
        return {f: e.get_json_data(escape_html) for f, e in self.items()}