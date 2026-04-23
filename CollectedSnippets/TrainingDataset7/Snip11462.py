def _check_unique(self, **kwargs):
        if self.unique:
            return [
                checks.Error(
                    "ManyToManyFields cannot be unique.",
                    obj=self,
                    id="fields.E330",
                )
            ]
        return []