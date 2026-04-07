def serialize(self):
        if self.value.tzinfo is not None and self.value.tzinfo != datetime.UTC:
            self.value = self.value.astimezone(datetime.UTC)
        imports = ["import datetime"]
        return repr(self.value), set(imports)