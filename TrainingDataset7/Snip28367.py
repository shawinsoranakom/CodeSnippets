def test_validates_with_replaced_field_not_specified(self):
        form = IncompleteCategoryFormWithFields(
            data={"name": "some name", "slug": "some-slug"}
        )
        self.assertIs(form.is_valid(), True)