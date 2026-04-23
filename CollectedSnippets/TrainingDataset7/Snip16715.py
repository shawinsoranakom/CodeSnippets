def assert_field_visible(self, response, field_name):
        self.assertContains(
            response, f'<div class="flex-container fieldBox field-{field_name}">'
        )