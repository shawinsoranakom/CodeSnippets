def test_save_new(self):
        """
        Make sure inlineformsets respect commit=False
        regression for #10750
        """
        # exclude some required field from the forms
        ChildFormSet = inlineformset_factory(
            School, Child, exclude=["father", "mother"]
        )
        school = School.objects.create(name="test")
        mother = Parent.objects.create(name="mother")
        father = Parent.objects.create(name="father")
        data = {
            "child_set-TOTAL_FORMS": "1",
            "child_set-INITIAL_FORMS": "0",
            "child_set-MAX_NUM_FORMS": "0",
            "child_set-0-name": "child",
        }
        formset = ChildFormSet(data, instance=school)
        self.assertIs(formset.is_valid(), True)
        objects = formset.save(commit=False)
        for obj in objects:
            obj.mother = mother
            obj.father = father
            obj.save()
        self.assertEqual(school.child_set.count(), 1)