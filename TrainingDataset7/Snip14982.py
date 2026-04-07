def get_context_data(self, **kwargs):
        return {
            "catalog": self.get_catalog(),
            "formats": get_formats(),
            "plural": self.get_plural(),
        }