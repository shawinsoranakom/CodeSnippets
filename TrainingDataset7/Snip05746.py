def action_checkbox(self, obj):
        """
        A list_display column containing a checkbox widget.
        """
        attrs = {
            "class": "action-select",
            "aria-label": format_html(
                _("Select this object for an action - {}"), str(obj)
            ),
        }
        checkbox = forms.CheckboxInput(attrs, lambda value: False)
        return checkbox.render(helpers.ACTION_CHECKBOX_NAME, str(obj.pk))