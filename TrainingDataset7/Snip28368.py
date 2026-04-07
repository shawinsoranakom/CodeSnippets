def test_validates_with_replaced_field_excluded(self):
        form = IncompleteCategoryFormWithExclude(
            data={"name": "some name", "slug": "some-slug"}
        )
        self.assertIs(form.is_valid(), True)