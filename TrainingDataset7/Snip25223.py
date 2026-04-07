def test_constraint_refs_inline_foreignkey_field(self):
        """
        Constraints that reference an InlineForeignKeyField should not be
        skipped from validation (#35676).
        """
        ChildFormSet = inlineformset_factory(
            Parent,
            Child,
            fk_name="mother",
            fields="__all__",
            extra=1,
        )
        father = Parent.objects.create(name="James")
        school = School.objects.create(name="Hogwarts")
        mother = Parent.objects.create(name="Lily")
        Child.objects.create(name="Harry", father=father, mother=mother, school=school)
        data = {
            "mothers_children-TOTAL_FORMS": "1",
            "mothers_children-INITIAL_FORMS": "0",
            "mothers_children-MIN_NUM_FORMS": "0",
            "mothers_children-MAX_NUM_FORMS": "1000",
            "mothers_children-0-id": "",
            "mothers_children-0-father": str(father.pk),
            "mothers_children-0-school": str(school.pk),
            "mothers_children-0-name": "Mary",
        }
        formset = ChildFormSet(instance=mother, data=data, queryset=None)
        self.assertFalse(formset.is_valid())
        self.assertEqual(
            formset.errors,
            [{"__all__": ["Constraint “unique_parents” is violated."]}],
        )