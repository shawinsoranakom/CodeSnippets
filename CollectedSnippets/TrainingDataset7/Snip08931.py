def next_page_number(self):
        return self.paginator.validate_number(self.number + 1)