def assertFormSetError(self, formset, form_index, field, errors, msg_prefix=""):
        """
        Similar to assertFormError() but for formsets.

        Use form_index=None to check the formset's non-form errors (in that
        case, you must also use field=None).
        Otherwise use an integer to check the formset's n-th form for errors.

        Other parameters are the same as assertFormError().
        """
        if form_index is None and field is not None:
            raise ValueError("You must use field=None with form_index=None.")

        if msg_prefix:
            msg_prefix += ": "
        errors = to_list(errors)

        if not formset.is_bound:
            self.fail(
                f"{msg_prefix}The formset {formset!r} is not bound, it will never have "
                f"any errors."
            )
        if form_index is not None and form_index >= formset.total_form_count():
            form_count = formset.total_form_count()
            form_or_forms = "forms" if form_count > 1 else "form"
            self.fail(
                f"{msg_prefix}The formset {formset!r} only has {form_count} "
                f"{form_or_forms}."
            )
        if form_index is not None:
            self._assert_form_error(
                formset.forms[form_index],
                field,
                errors,
                msg_prefix,
                formset=formset,
                form_index=form_index,
            )
        else:
            formset_errors = formset.non_form_errors()
            if formset_errors == errors:
                # Skip assertion if errors already match.
                return

            failure_message = f"The non-form errors of formset {formset!r} don't match."
            self.assertEqual(formset_errors, errors, msg_prefix + failure_message)