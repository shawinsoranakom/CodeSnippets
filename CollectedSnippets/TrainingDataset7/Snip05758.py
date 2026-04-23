def get_search_results(self, request, queryset, search_term):
        """
        Return a tuple containing a queryset to implement the search
        and a boolean indicating if the results may contain duplicates.
        """

        # Apply keyword searches.
        def construct_search(field_name):
            """
            Return a tuple of (lookup, field_to_validate).

            field_to_validate is set for non-text exact lookups so that
            invalid search terms can be skipped (preserving index usage).
            """
            if field_name.startswith("^"):
                return "%s__istartswith" % field_name.removeprefix("^"), None
            elif field_name.startswith("="):
                return "%s__iexact" % field_name.removeprefix("="), None
            elif field_name.startswith("@"):
                return "%s__search" % field_name.removeprefix("@"), None
            # Use field_name if it includes a lookup.
            opts = queryset.model._meta
            lookup_fields = field_name.split(LOOKUP_SEP)
            # Go through the fields, following all relations.
            prev_field = None
            for path_part in lookup_fields:
                if path_part == "pk":
                    path_part = opts.pk.name
                try:
                    field = opts.get_field(path_part)
                except FieldDoesNotExist:
                    # Use valid query lookups.
                    if prev_field and prev_field.get_lookup(path_part):
                        if path_part == "exact" and not isinstance(
                            prev_field, (models.CharField, models.TextField)
                        ):
                            # Use prev_field to validate the search term.
                            return field_name, prev_field
                        return field_name, None
                else:
                    prev_field = field
                    if hasattr(field, "path_infos"):
                        # Update opts to follow the relation.
                        opts = field.path_infos[-1].to_opts
            # Otherwise, use the field with icontains.
            return "%s__icontains" % field_name, None

        may_have_duplicates = False
        search_fields = self.get_search_fields(request)
        if search_fields and search_term:
            orm_lookups = []
            for field in search_fields:
                orm_lookups.append(construct_search(str(field)))

            term_queries = []
            for bit in smart_split(search_term):
                if bit.startswith(('"', "'")) and bit[0] == bit[-1]:
                    bit = unescape_string_literal(bit)
                # Build term lookups, skipping values invalid for their field.
                bit_lookups = []
                for orm_lookup, validate_field in orm_lookups:
                    if validate_field is not None:
                        formfield = validate_field.formfield()
                        try:
                            if formfield is not None:
                                value = formfield.to_python(bit)
                            else:
                                # Fields like AutoField lack a form field.
                                value = validate_field.to_python(bit)
                        except ValidationError:
                            # Skip this lookup for invalid values.
                            continue
                    else:
                        value = bit
                    bit_lookups.append((orm_lookup, value))
                if bit_lookups:
                    or_queries = models.Q.create(bit_lookups, connector=models.Q.OR)
                    term_queries.append(or_queries)
                else:
                    # No valid lookups: add a filter that returns nothing.
                    term_queries.append(models.Q(pk__in=[]))
            if term_queries:
                queryset = queryset.filter(models.Q.create(term_queries))
            may_have_duplicates |= any(
                lookup_spawns_duplicates(self.opts, search_spec)
                for search_spec, _ in orm_lookups
            )
        return queryset, may_have_duplicates