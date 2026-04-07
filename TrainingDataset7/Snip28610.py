def test_initial_data(self):
        user = User.objects.create(username="bibi", serial=1)
        UserSite.objects.create(user=user, data=7)
        FormSet = inlineformset_factory(User, UserSite, extra=2, fields="__all__")

        formset = FormSet(instance=user, initial=[{"data": 41}, {"data": 42}])
        self.assertEqual(formset.forms[0].initial["data"], 7)
        self.assertEqual(formset.extra_forms[0].initial["data"], 41)
        self.assertIn('value="42"', formset.extra_forms[1].as_p())