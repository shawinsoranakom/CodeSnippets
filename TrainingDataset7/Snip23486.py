def test_save_new_uses_form_save(self):
        class SaveTestForm(forms.ModelForm):
            def save(self, *args, **kwargs):
                self.instance.saved_by = "custom method"
                return super().save(*args, **kwargs)

        Formset = generic_inlineformset_factory(
            ForProxyModelModel, fields="__all__", form=SaveTestForm
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
        new_obj = formset.save()[0]
        self.assertEqual(new_obj.saved_by, "custom method")