def test_initial_data(self):
        User.objects.create(username="bibi", serial=1)
        Formset = modelformset_factory(User, fields="__all__", extra=2)
        formset = Formset(initial=[{"username": "apollo11"}, {"username": "apollo12"}])
        self.assertEqual(formset.forms[0].initial["username"], "bibi")
        self.assertEqual(formset.extra_forms[0].initial["username"], "apollo11")
        self.assertIn('value="apollo12"', formset.extra_forms[1].as_p())