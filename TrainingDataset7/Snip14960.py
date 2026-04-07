def post(self, request, *args, **kwargs):
        # Set self.object before the usual form processing flow.
        # Inlined because having DeletionMixin as the first base, for
        # get_success_url(), makes leveraging super() with ProcessFormView
        # overly complex.
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)