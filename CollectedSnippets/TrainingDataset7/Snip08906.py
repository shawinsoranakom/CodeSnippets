def __iter__(self):
        for page_number in self.page_range:
            yield self.page(page_number)