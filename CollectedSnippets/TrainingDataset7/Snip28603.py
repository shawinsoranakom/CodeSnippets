def test_formset_over_inherited_model(self):
        """
        A formset over a ForeignKey with a to_field can be saved.
        """
        Form = modelform_factory(Restaurant, fields="__all__")
        FormSet = inlineformset_factory(Restaurant, Manager, fields="__all__")

        # Instantiate the Form and FormSet to prove
        # you can create a form with no data
        form = Form()
        form_set = FormSet(instance=Restaurant())

        # Now create a new Restaurant and Manager instance
        data = {
            "name": "Guido's House of Pasta",
            "manager_set-TOTAL_FORMS": "1",
            "manager_set-INITIAL_FORMS": "0",
            "manager_set-MAX_NUM_FORMS": "0",
            "manager_set-0-name": "Guido Van Rossum",
        }
        restaurant = User()
        form = Form(data)
        if form.is_valid():
            restaurant = form.save()
        else:
            self.fail("Errors found on form:%s" % form_set)

        form_set = FormSet(data, instance=restaurant)
        if form_set.is_valid():
            form_set.save()
            manager = Manager.objects.values()
            self.assertEqual(manager[0]["name"], "Guido Van Rossum")
        else:
            self.fail("Errors found on formset:%s" % form_set.errors)

        # Now update the Manager instance
        data = {
            "manager_set-TOTAL_FORMS": "1",
            "manager_set-INITIAL_FORMS": "1",
            "manager_set-MAX_NUM_FORMS": "0",
            "manager_set-0-id": str(manager[0]["id"]),
            "manager_set-0-name": "Terry Gilliam",
        }
        form_set = FormSet(data, instance=restaurant)
        if form_set.is_valid():
            form_set.save()
            manager = Manager.objects.values()
            self.assertEqual(manager[0]["name"], "Terry Gilliam")
        else:
            self.fail("Errors found on formset:%s" % form_set.errors)

        # Now add a new Manager instance
        data = {
            "manager_set-TOTAL_FORMS": "2",
            "manager_set-INITIAL_FORMS": "1",
            "manager_set-MAX_NUM_FORMS": "0",
            "manager_set-0-id": str(manager[0]["id"]),
            "manager_set-0-name": "Terry Gilliam",
            "manager_set-1-name": "John Cleese",
        }
        form_set = FormSet(data, instance=restaurant)
        if form_set.is_valid():
            form_set.save()
            manager = Manager.objects.values().order_by("name")
            self.assertEqual(manager[0]["name"], "John Cleese")
            self.assertEqual(manager[1]["name"], "Terry Gilliam")
        else:
            self.fail("Errors found on formset:%s" % form_set.errors)