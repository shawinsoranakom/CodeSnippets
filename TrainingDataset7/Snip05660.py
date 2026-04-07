def __iter__(self):
        for i, field in enumerate(self.fields):
            if field in self.readonly_fields:
                yield AdminReadonlyField(
                    self.form, field, is_first=(i == 0), model_admin=self.model_admin
                )
            else:
                yield AdminField(self.form, field, is_first=(i == 0))