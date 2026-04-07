def _assert_form_error(
        self, form, field, errors, msg_prefix, formset=None, form_index=None
    ):
        if not form.is_bound:
            self.fail(
                "%sThe %s is not bound, it will never have any errors."
                % (msg_prefix, self._form_repr(form, formset, form_index))
            )

        if field is not None and field not in form.fields:
            self.fail(
                "%sThe %s does not contain the field %r."
                % (msg_prefix, self._form_repr(form, formset, form_index), field)
            )
        field_errors = (
            form.non_field_errors() if field is None else form.errors.get(field, [])
        )

        if field_errors == errors:
            return

        # Use assertEqual to show detailed diff if errors don't match.
        if field is None:
            failure_message = "The non-field errors of %s don't match." % (
                self._form_repr(form, formset, form_index),
            )
        else:
            failure_message = "The errors of field %r on %s don't match." % (
                field,
                self._form_repr(form, formset, form_index),
            )
        self.assertEqual(field_errors, errors, msg_prefix + failure_message)