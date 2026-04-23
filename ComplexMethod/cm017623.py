def get_filters(self, request):
        lookup_params = self.get_filters_params()
        may_have_duplicates = False
        has_active_filters = False

        for key, value_list in lookup_params.items():
            for value in value_list:
                if not self.model_admin.lookup_allowed(key, value, request):
                    raise DisallowedModelAdminLookup(f"Filtering by {key} not allowed")

        filter_specs = []
        for list_filter in self.list_filter:
            lookup_params_count = len(lookup_params)
            if callable(list_filter):
                # This is simply a custom list filter class.
                spec = list_filter(request, lookup_params, self.model, self.model_admin)
            else:
                field_path = None
                if isinstance(list_filter, (tuple, list)):
                    # This is a custom FieldListFilter class for a given field.
                    field, field_list_filter_class = list_filter
                else:
                    # This is simply a field name, so use the default
                    # FieldListFilter class that has been registered for the
                    # type of the given field.
                    field, field_list_filter_class = list_filter, FieldListFilter.create
                if not isinstance(field, Field):
                    field_path = field
                    field = get_fields_from_path(self.model, field_path)[-1]

                spec = field_list_filter_class(
                    field,
                    request,
                    lookup_params,
                    self.model,
                    self.model_admin,
                    field_path=field_path,
                )
                # field_list_filter_class removes any lookup_params it
                # processes. If that happened, check if duplicates should be
                # removed.
                if lookup_params_count > len(lookup_params):
                    may_have_duplicates |= lookup_spawns_duplicates(
                        self.lookup_opts,
                        field_path,
                    )
            if spec and spec.has_output():
                filter_specs.append(spec)
                if lookup_params_count > len(lookup_params):
                    has_active_filters = True

        if self.date_hierarchy:
            # Create bounded lookup parameters so that the query is more
            # efficient.
            year = lookup_params.pop("%s__year" % self.date_hierarchy, None)
            if year is not None:
                month = lookup_params.pop("%s__month" % self.date_hierarchy, None)
                day = lookup_params.pop("%s__day" % self.date_hierarchy, None)
                try:
                    from_date = datetime(
                        int(year[-1]),
                        int(month[-1] if month is not None else 1),
                        int(day[-1] if day is not None else 1),
                    )
                except ValueError as e:
                    raise IncorrectLookupParameters(e) from e
                if day:
                    to_date = from_date + timedelta(days=1)
                elif month:
                    # In this branch, from_date will always be the first of a
                    # month, so advancing 32 days gives the next month.
                    to_date = (from_date + timedelta(days=32)).replace(day=1)
                else:
                    to_date = from_date.replace(year=from_date.year + 1)
                if settings.USE_TZ:
                    from_date = make_aware(from_date)
                    to_date = make_aware(to_date)
                lookup_params.update(
                    {
                        "%s__gte" % self.date_hierarchy: [from_date],
                        "%s__lt" % self.date_hierarchy: [to_date],
                    }
                )

        # At this point, all the parameters used by the various ListFilters
        # have been removed from lookup_params, which now only contains other
        # parameters passed via the query string. We now loop through the
        # remaining parameters both to ensure that all the parameters are valid
        # fields and to determine if at least one of them spawns duplicates. If
        # the lookup parameters aren't real fields, then bail out.
        try:
            for key, value in lookup_params.items():
                lookup_params[key] = prepare_lookup_value(key, value)
                may_have_duplicates |= lookup_spawns_duplicates(self.lookup_opts, key)
            return (
                filter_specs,
                bool(filter_specs),
                lookup_params,
                may_have_duplicates,
                has_active_filters,
            )
        except FieldDoesNotExist as e:
            raise IncorrectLookupParameters(e) from e