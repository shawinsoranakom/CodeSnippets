def __init__(
        self,
        queryset,
        *,
        empty_label="---------",
        required=True,
        widget=None,
        label=None,
        initial=None,
        help_text="",
        to_field_name=None,
        limit_choices_to=None,
        blank=False,
        **kwargs,
    ):
        # Call Field instead of ChoiceField __init__() because we don't need
        # ChoiceField.__init__().
        Field.__init__(
            self,
            required=required,
            widget=widget,
            label=label,
            initial=initial,
            help_text=help_text,
            **kwargs,
        )
        if (required and initial is not None) or (
            isinstance(self.widget, RadioSelect) and not blank
        ):
            self.empty_label = None
        else:
            self.empty_label = empty_label
        self.queryset = queryset
        self.limit_choices_to = limit_choices_to  # limit the queryset later.
        self.to_field_name = to_field_name