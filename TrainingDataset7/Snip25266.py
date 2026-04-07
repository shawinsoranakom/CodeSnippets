def test_django_table_names_retval_type(self):
        # Table name is a list #15216
        tl = connection.introspection.django_table_names(only_existing=True)
        self.assertIs(type(tl), list)
        tl = connection.introspection.django_table_names(only_existing=False)
        self.assertIs(type(tl), list)