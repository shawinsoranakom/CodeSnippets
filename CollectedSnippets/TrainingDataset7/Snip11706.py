def _resolve_output_field(self):
        source = self.get_source_expressions()[0]
        return source.output_field