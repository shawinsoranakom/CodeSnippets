def _check_max_length_warning(self):
        if self.max_length is not None:
            return [
                checks.Warning(
                    "'max_length' is ignored when used with %s."
                    % self.__class__.__name__,
                    hint="Remove 'max_length' from field",
                    obj=self,
                    id="fields.W122",
                )
            ]
        return []