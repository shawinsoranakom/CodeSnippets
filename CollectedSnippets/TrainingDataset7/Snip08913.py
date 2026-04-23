def get_elided_page_range(self, number=1, *, on_each_side=3, on_ends=2):
        number = self.validate_number(number)
        yield from self._get_elided_page_range(
            number, self.num_pages, self.page_range, on_each_side, on_ends
        )