def initial_form_count(self):
        if self.save_as_new:
            return 0
        return super().initial_form_count()