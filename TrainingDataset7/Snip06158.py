def create_usable_password_field(help_text=usable_password_help_text):
        return forms.ChoiceField(
            label=_("Password-based authentication"),
            required=False,
            initial="true",
            choices={"true": _("Enabled"), "false": _("Disabled")},
            widget=forms.RadioSelect(attrs={"class": "radiolist"}),
            help_text=help_text,
        )