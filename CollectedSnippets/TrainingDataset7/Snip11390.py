def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if self._limit_choices_to:
            kwargs["limit_choices_to"] = self._limit_choices_to
        if self._related_name is not None:
            kwargs["related_name"] = self._related_name
        if self._related_query_name is not None:
            kwargs["related_query_name"] = self._related_query_name
        return name, path, args, kwargs