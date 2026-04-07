def _should_delete_form(self, form):
        return hasattr(form, "should_delete") and form.should_delete()