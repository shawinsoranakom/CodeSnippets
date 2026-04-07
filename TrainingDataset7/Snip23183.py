def test_m2m_field_exclusion(self):
        # Issue 12337. save_instance should honor the passed-in exclude
        # keyword.
        opt1 = ChoiceOptionModel.objects.create(id=1, name="default")
        opt2 = ChoiceOptionModel.objects.create(id=2, name="option 2")
        opt3 = ChoiceOptionModel.objects.create(id=3, name="option 3")
        initial = {
            "choice": opt1,
            "choice_int": opt1,
        }
        data = {
            "choice": opt2.pk,
            "choice_int": opt2.pk,
            "multi_choice": "string data!",
            "multi_choice_int": [opt1.pk],
        }
        instance = ChoiceFieldModel.objects.create(**initial)
        instance.multi_choice.set([opt2, opt3])
        instance.multi_choice_int.set([opt2, opt3])
        form = ChoiceFieldExclusionForm(data=data, instance=instance)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["multi_choice"], data["multi_choice"])
        form.save()
        self.assertEqual(form.instance.choice.pk, data["choice"])
        self.assertEqual(form.instance.choice_int.pk, data["choice_int"])
        self.assertEqual(list(form.instance.multi_choice.all()), [opt2, opt3])
        self.assertEqual(
            [obj.pk for obj in form.instance.multi_choice_int.all()],
            data["multi_choice_int"],
        )