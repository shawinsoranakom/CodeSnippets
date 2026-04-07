def get_form(self, *args, **kwargs):
        self.get_form_called_count += 1
        return super().get_form(*args, **kwargs)