def test_change_list_column_field_classes(self):
        response = self.client.get(reverse("admin:admin_views_article_changelist"))
        # callables display the callable name.
        self.assertContains(response, "column-callable_year")
        self.assertContains(response, "field-callable_year")
        # lambdas display as "lambda" + index that they appear in list_display.
        self.assertContains(response, "column-lambda8")
        self.assertContains(response, "field-lambda8")