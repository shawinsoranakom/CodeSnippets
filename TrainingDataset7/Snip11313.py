def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        del kwargs["blank"]
        del kwargs["editable"]
        kwargs["db_persist"] = self.db_persist
        kwargs["expression"] = self.expression
        kwargs["output_field"] = self.output_field
        return name, path, args, kwargs