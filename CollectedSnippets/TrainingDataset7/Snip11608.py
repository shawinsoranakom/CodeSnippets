def get_choices(
        self,
        include_blank=True,
        blank_choice=BLANK_CHOICE_DASH,
        limit_choices_to=None,
        ordering=(),
    ):
        """
        Return choices with a default blank choices included, for use
        as <select> choices for this field.

        Analog of django.db.models.fields.Field.get_choices(), provided
        initially for utilization by RelatedFieldListFilter.
        """
        limit_choices_to = limit_choices_to or self.limit_choices_to
        qs = self.related_model._default_manager.complex_filter(limit_choices_to)
        if ordering:
            qs = qs.order_by(*ordering)
        return (blank_choice if include_blank else []) + [(x.pk, str(x)) for x in qs]