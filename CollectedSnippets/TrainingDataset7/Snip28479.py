def test_check_constraint_refs_excluded_field_attname(self):
        left = AttnameConstraintsModel.objects.create()
        instance = AttnameConstraintsModel.objects.create(left=left)
        data = {
            "left": str(left.id),
            "right": "",
        }
        AttnameConstraintsModelForm = modelform_factory(
            AttnameConstraintsModel, fields="__all__"
        )
        full_form = AttnameConstraintsModelForm(data, instance=instance)
        self.assertFalse(full_form.is_valid())
        self.assertEqual(full_form.errors, {"right": ["This field is required."]})