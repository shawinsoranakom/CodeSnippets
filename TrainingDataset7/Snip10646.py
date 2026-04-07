def _perform_date_checks(self, date_checks):
        errors = {}
        for model_class, lookup_type, field, unique_for in date_checks:
            lookup_kwargs = {}
            # there's a ticket to add a date lookup, we can remove this special
            # case if that makes it's way in
            date = getattr(self, unique_for)
            if date is None:
                continue
            if lookup_type == "date":
                lookup_kwargs["%s__day" % unique_for] = date.day
                lookup_kwargs["%s__month" % unique_for] = date.month
                lookup_kwargs["%s__year" % unique_for] = date.year
            else:
                lookup_kwargs["%s__%s" % (unique_for, lookup_type)] = getattr(
                    date, lookup_type
                )
            lookup_kwargs[field] = getattr(self, field)

            qs = model_class._default_manager.filter(**lookup_kwargs)
            # Exclude the current object from the query if we are editing an
            # instance (as opposed to creating a new one)
            if not self._state.adding and self._is_pk_set():
                qs = qs.exclude(pk=self.pk)

            if qs.exists():
                errors.setdefault(field, []).append(
                    self.date_error_message(lookup_type, field, unique_for)
                )
        return errors