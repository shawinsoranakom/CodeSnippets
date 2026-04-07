def test_clean_does_deduplicate_values(self):
        class PersonForm(forms.Form):
            persons = forms.ModelMultipleChoiceField(queryset=Person.objects.all())

        person1 = Person.objects.create(name="Person 1")
        form = PersonForm(data={})
        queryset = form.fields["persons"].clean([str(person1.pk)] * 50)
        sql, params = queryset.query.sql_with_params()
        self.assertEqual(len(params), 1)