def assert_fieldline_hidden(self, response):
        self.assertContains(
            response,
            "<div class="
            '"form-row flex-container form-multiline hidden field-first field-second">',
        )