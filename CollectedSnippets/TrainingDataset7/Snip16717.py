def assert_fieldline_visible(self, response):
        self.assertContains(
            response,
            "<div class="
            '"form-row flex-container form-multiline field-first field-second">',
        )