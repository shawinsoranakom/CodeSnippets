def test_table_headers(self):
        tests = [
            ("Method", 1),
            ("Arguments", 1),
            ("Description", 2),
            ("Field", 1),
            ("Type", 1),
            ("Method", 1),
        ]
        for table_header, count in tests:
            self.assertContains(
                self.response, f'<th scope="col">{table_header}</th>', count=count
            )