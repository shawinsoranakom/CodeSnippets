def next_page_number(self):
        if not self.has_next():
            return None
        return super().next_page_number()