def previous_page_number(self):
        if not self.has_previous():
            return None
        return super().previous_page_number()