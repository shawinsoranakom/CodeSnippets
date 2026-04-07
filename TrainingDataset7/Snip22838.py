def test_multivalue_initial_data(self):
        """
        #23674 -- invalid initial data should not break form.changed_data()
        """

        class DateAgeField(MultiValueField):
            def __init__(self, fields=(), *args, **kwargs):
                fields = (DateField(label="Date"), IntegerField(label="Age"))
                super().__init__(fields=fields, *args, **kwargs)

        class DateAgeForm(Form):
            date_age = DateAgeField()

        data = {"date_age": ["1998-12-06", 16]}
        form = DateAgeForm(data, initial={"date_age": ["200-10-10", 14]})
        self.assertTrue(form.has_changed())