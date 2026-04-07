def test_delete_already_deleted(self):
        u = User.objects.create(username="foo", serial=1)
        us = UserSite.objects.create(user=u, data=7)
        formset_cls = inlineformset_factory(User, UserSite, fields="__all__")
        data = {
            "serial": "1",
            "username": "foo",
            "usersite_set-TOTAL_FORMS": "1",
            "usersite_set-INITIAL_FORMS": "1",
            "usersite_set-MAX_NUM_FORMS": "1",
            "usersite_set-0-id": str(us.pk),
            "usersite_set-0-data": "7",
            "usersite_set-0-user": "foo",
            "usersite_set-0-DELETE": "1",
        }
        formset = formset_cls(data, instance=u)
        us.delete()
        self.assertTrue(formset.is_valid())
        formset.save()
        self.assertEqual(UserSite.objects.count(), 0)