def test_method_data_types(self):
        company = Company.objects.create(name="Django")
        person = Person.objects.create(
            first_name="Human", last_name="User", company=company
        )
        self.assertEqual(
            get_return_data_type(person.get_status_count.__name__), "Integer"
        )
        self.assertEqual(get_return_data_type(person.get_groups_list.__name__), "List")