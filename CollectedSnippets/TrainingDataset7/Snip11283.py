def _check_primary_key(self):
        if self._primary_key_set_explicitly:
            return [
                checks.Error(
                    "'primary_key' is not a valid argument for a %s."
                    % self.__class__.__name__,
                    obj=self,
                    id="fields.E201",
                )
            ]
        else:
            return []