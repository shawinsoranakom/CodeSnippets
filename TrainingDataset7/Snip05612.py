def queryset(self, request, queryset):
        try:
            q_object = build_q_object_from_lookup_parameters(self.used_parameters)
            return queryset.filter(q_object)
        except (ValueError, ValidationError) as e:
            # Fields may raise a ValueError or ValidationError when converting
            # the parameters to the correct type.
            raise IncorrectLookupParameters(e)