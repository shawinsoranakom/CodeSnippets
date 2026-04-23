def test_custom_pk_create(self):
        """
        New objects can be created both with pk and the custom name
        """
        Employee.objects.create(employee_code=1234, first_name="Foo", last_name="Bar")
        Employee.objects.create(pk=1235, first_name="Foo", last_name="Baz")
        Business.objects.create(name="Bears")
        Business.objects.create(pk="Tears")