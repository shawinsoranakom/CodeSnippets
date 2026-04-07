def get_redirect_field_name(self, view_func):
        return getattr(view_func, "redirect_field_name", self.redirect_field_name)