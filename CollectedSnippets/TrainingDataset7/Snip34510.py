def _engine(self, **kwargs):
        return Engine(debug=self.debug_engine, **kwargs)