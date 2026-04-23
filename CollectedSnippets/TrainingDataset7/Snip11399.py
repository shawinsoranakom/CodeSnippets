def target_field(self):
        """
        When filtering against this relation, return the field on the remote
        model against which the filtering should happen.
        """
        target_fields = self.path_infos[-1].target_fields
        if len(target_fields) > 1:
            raise exceptions.FieldError(
                "The relation has multiple target fields, but only single target field "
                "was asked for"
            )
        return target_fields[0]