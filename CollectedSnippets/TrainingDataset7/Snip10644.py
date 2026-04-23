def _get_unique_checks(self, exclude=None, include_meta_constraints=False):
        """
        Return a list of checks to perform. Since validate_unique() could be
        called from a ModelForm, some fields may have been excluded; we can't
        perform a unique check on a model that is missing fields involved
        in that check. Fields that did not validate should also be excluded,
        but they need to be passed in via the exclude argument.
        """
        if exclude is None:
            exclude = set()
        unique_checks = []

        unique_togethers = [(self.__class__, self._meta.unique_together)]
        constraints = []
        if include_meta_constraints:
            constraints = [(self.__class__, self._meta.total_unique_constraints)]
        for parent_class in self._meta.all_parents:
            if parent_class._meta.unique_together:
                unique_togethers.append(
                    (parent_class, parent_class._meta.unique_together)
                )
            if include_meta_constraints and parent_class._meta.total_unique_constraints:
                constraints.append(
                    (parent_class, parent_class._meta.total_unique_constraints)
                )

        for model_class, unique_together in unique_togethers:
            for check in unique_together:
                if not any(name in exclude for name in check):
                    # Add the check if the field isn't excluded.
                    unique_checks.append((model_class, tuple(check)))

        if include_meta_constraints:
            for model_class, model_constraints in constraints:
                for constraint in model_constraints:
                    if not any(name in exclude for name in constraint.fields):
                        unique_checks.append((model_class, constraint.fields))

        # These are checks for the unique_for_<date/year/month>.
        date_checks = []

        # Gather a list of checks for fields declared as unique and add them to
        # the list of checks.

        fields_with_class = [(self.__class__, self._meta.local_fields)]
        for parent_class in self._meta.all_parents:
            fields_with_class.append((parent_class, parent_class._meta.local_fields))

        for model_class, fields in fields_with_class:
            for f in fields:
                name = f.name
                if name in exclude:
                    continue
                if isinstance(f, CompositePrimaryKey):
                    names = tuple(field.name for field in f.fields)
                    if exclude.isdisjoint(names):
                        unique_checks.append((model_class, names))
                    continue
                if f.unique:
                    unique_checks.append((model_class, (name,)))
                if f.unique_for_date and f.unique_for_date not in exclude:
                    date_checks.append((model_class, "date", name, f.unique_for_date))
                if f.unique_for_year and f.unique_for_year not in exclude:
                    date_checks.append((model_class, "year", name, f.unique_for_year))
                if f.unique_for_month and f.unique_for_month not in exclude:
                    date_checks.append((model_class, "month", name, f.unique_for_month))
        return unique_checks, date_checks