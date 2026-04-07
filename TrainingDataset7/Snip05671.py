def fields(self):
        fk = getattr(self.formset, "fk", None)
        empty_form = self.formset.empty_form
        meta_labels = empty_form._meta.labels or {}
        meta_help_texts = empty_form._meta.help_texts or {}
        for i, field_name in enumerate(flatten_fieldsets(self.fieldsets)):
            if fk and fk.name == field_name:
                continue
            if not self.has_change_permission or field_name in self.readonly_fields:
                form_field = empty_form.fields.get(field_name)
                widget_is_hidden = False
                if form_field is not None:
                    widget_is_hidden = form_field.widget.is_hidden
                yield {
                    "name": field_name,
                    "label": meta_labels.get(field_name)
                    or label_for_field(
                        field_name,
                        self.opts.model,
                        self.opts,
                        form=empty_form,
                    ),
                    "widget": {"is_hidden": widget_is_hidden},
                    "required": False,
                    "help_text": meta_help_texts.get(field_name)
                    or help_text_for_field(field_name, self.opts.model),
                }
            else:
                form_field = empty_form.fields[field_name]
                label = form_field.label
                if label is None:
                    label = label_for_field(
                        field_name, self.opts.model, self.opts, form=empty_form
                    )
                yield {
                    "name": field_name,
                    "label": label,
                    "widget": form_field.widget,
                    "required": form_field.required,
                    "help_text": form_field.help_text,
                }