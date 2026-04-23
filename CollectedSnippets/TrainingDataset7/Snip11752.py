def _resolve_output_field(self):
        sources = self.get_source_expressions()
        return sources[0].output_field