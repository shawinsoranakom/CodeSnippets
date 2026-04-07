def test_model_formset_with_initial_model_instance(self):
        # has_changed should compare model instance and primary key
        # see #18898
        FormSet = modelformset_factory(Poem, fields="__all__")
        john_milton = Poet(name="John Milton")
        john_milton.save()
        data = {
            "form-TOTAL_FORMS": 1,
            "form-INITIAL_FORMS": 0,
            "form-MAX_NUM_FORMS": "",
            "form-0-name": "",
            "form-0-poet": str(john_milton.id),
        }
        formset = FormSet(initial=[{"poet": john_milton}], data=data)
        self.assertFalse(formset.extra_forms[0].has_changed())