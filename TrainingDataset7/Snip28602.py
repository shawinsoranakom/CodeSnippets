def test_formset_over_to_field(self):
        """
        A formset over a ForeignKey with a to_field can be saved.
        """
        Form = modelform_factory(User, fields="__all__")
        FormSet = inlineformset_factory(User, UserSite, fields="__all__")

        # Instantiate the Form and FormSet to prove
        # you can create a form with no data
        form = Form()
        form_set = FormSet(instance=User())

        # Now create a new User and UserSite instance
        data = {
            "serial": "1",
            "username": "apollo13",
            "usersite_set-TOTAL_FORMS": "1",
            "usersite_set-INITIAL_FORMS": "0",
            "usersite_set-MAX_NUM_FORMS": "0",
            "usersite_set-0-data": "10",
            "usersite_set-0-user": "apollo13",
        }
        user = User()
        form = Form(data)
        if form.is_valid():
            user = form.save()
        else:
            self.fail("Errors found on form:%s" % form_set)

        form_set = FormSet(data, instance=user)
        if form_set.is_valid():
            form_set.save()
            usersite = UserSite.objects.values()
            self.assertEqual(usersite[0]["data"], 10)
            self.assertEqual(usersite[0]["user_id"], "apollo13")
        else:
            self.fail("Errors found on formset:%s" % form_set.errors)

        # Now update the UserSite instance
        data = {
            "usersite_set-TOTAL_FORMS": "1",
            "usersite_set-INITIAL_FORMS": "1",
            "usersite_set-MAX_NUM_FORMS": "0",
            "usersite_set-0-id": str(usersite[0]["id"]),
            "usersite_set-0-data": "11",
            "usersite_set-0-user": "apollo13",
        }
        form_set = FormSet(data, instance=user)
        if form_set.is_valid():
            form_set.save()
            usersite = UserSite.objects.values()
            self.assertEqual(usersite[0]["data"], 11)
            self.assertEqual(usersite[0]["user_id"], "apollo13")
        else:
            self.fail("Errors found on formset:%s" % form_set.errors)

        # Now add a new UserSite instance
        data = {
            "usersite_set-TOTAL_FORMS": "2",
            "usersite_set-INITIAL_FORMS": "1",
            "usersite_set-MAX_NUM_FORMS": "0",
            "usersite_set-0-id": str(usersite[0]["id"]),
            "usersite_set-0-data": "11",
            "usersite_set-0-user": "apollo13",
            "usersite_set-1-data": "42",
            "usersite_set-1-user": "apollo13",
        }
        form_set = FormSet(data, instance=user)
        if form_set.is_valid():
            form_set.save()
            usersite = UserSite.objects.values().order_by("data")
            self.assertEqual(usersite[0]["data"], 11)
            self.assertEqual(usersite[0]["user_id"], "apollo13")
            self.assertEqual(usersite[1]["data"], 42)
            self.assertEqual(usersite[1]["user_id"], "apollo13")
        else:
            self.fail("Errors found on formset:%s" % form_set.errors)