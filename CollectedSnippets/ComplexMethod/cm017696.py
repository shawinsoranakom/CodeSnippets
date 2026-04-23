def build_widget_attrs(self, attrs, widget=None):
        widget = widget or self.field.widget
        attrs = dict(attrs)  # Copy attrs to avoid modifying the argument.
        if (
            widget.use_required_attribute(self.initial)
            and self.field.required
            and self.form.use_required_attribute
        ):
            # MultiValueField has require_all_fields: if False, fall back
            # on subfields.
            if (
                hasattr(self.field, "require_all_fields")
                and not self.field.require_all_fields
                and isinstance(self.field.widget, MultiWidget)
            ):
                for subfield, subwidget in zip(self.field.fields, widget.widgets):
                    subwidget.attrs["required"] = (
                        subwidget.use_required_attribute(self.initial)
                        and subfield.required
                    )
            else:
                attrs["required"] = True
        if self.field.disabled:
            attrs["disabled"] = True
        if not widget.is_hidden and self.errors:
            attrs["aria-invalid"] = "true"
        # Preserve aria-describedby provided by the attrs argument so user
        # can set the desired order.
        if not attrs.get("aria-describedby") and not self.use_fieldset:
            if aria_describedby := self.aria_describedby:
                attrs["aria-describedby"] = aria_describedby
        return attrs