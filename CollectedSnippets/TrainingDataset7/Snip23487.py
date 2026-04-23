def test_save_new_for_proxy(self):
        Formset = generic_inlineformset_factory(
            ForProxyModelModel, fields="__all__", for_concrete_model=False
        )
        instance = ProxyRelatedModel.objects.create()
        data = {
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "0",
            "form-MAX_NUM_FORMS": "",
            "form-0-title": "foo",
        }
        formset = Formset(data, instance=instance, prefix="form")
        self.assertTrue(formset.is_valid())
        (new_obj,) = formset.save()
        self.assertEqual(new_obj.obj, instance)