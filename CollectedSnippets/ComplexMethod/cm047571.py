def check_field_access_rights(self, operation: str, field_names: list[str] | None) -> list[str]:
        """Check the user access rights on the given fields.

        If `field_names` is not provided, we list accessible fields to the user.
        Otherwise, an error is raised if we try to access a forbidden field.
        Note that this function ignores unknown (virtual) fields.

        :param operation: one of ``create``, ``read``, ``write``, ``unlink``
        :param field_names: names of the fields
        :return: provided fields if fields is truthy (or the fields
          readable by the current user).
        :raise AccessError: if the user is not allowed to access
          the provided fields.
        """
        if self.env.su:
            return field_names or list(self._fields)

        if not field_names:
            return [
                field_name
                for field_name, field in self._fields.items()
                if self._has_field_access(field, operation)
            ]

        for field_name in field_names:
            # Unknown (or virtual) fields are considered accessible because they will not be read and nothing will be written to them.
            field = self._fields.get(field_name)
            if field is None:
                continue
            self._check_field_access(field, operation)
        return field_names