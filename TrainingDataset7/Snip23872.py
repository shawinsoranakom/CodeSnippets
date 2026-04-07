def form_valid(self, form):
        form.add_error(None, "There is an error")
        return self.form_invalid(form)