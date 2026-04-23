def test_formfield_initial(self):
        # If the model has default values for some fields, they are used as the
        # formfield initial values.
        class DefaultsForm(ModelForm):
            class Meta:
                model = Defaults
                fields = "__all__"

        self.assertEqual(DefaultsForm().fields["name"].initial, "class default value")
        self.assertEqual(
            DefaultsForm().fields["def_date"].initial, datetime.date(1980, 1, 1)
        )
        self.assertEqual(DefaultsForm().fields["value"].initial, 42)
        r1 = DefaultsForm()["callable_default"].as_widget()
        r2 = DefaultsForm()["callable_default"].as_widget()
        self.assertNotEqual(r1, r2)

        # In a ModelForm that is passed an instance, the initial values come
        # from the instance's values, not the model's defaults.
        foo_instance = Defaults(
            name="instance value", def_date=datetime.date(1969, 4, 4), value=12
        )
        instance_form = DefaultsForm(instance=foo_instance)
        self.assertEqual(instance_form.initial["name"], "instance value")
        self.assertEqual(instance_form.initial["def_date"], datetime.date(1969, 4, 4))
        self.assertEqual(instance_form.initial["value"], 12)

        from django.forms import CharField

        class ExcludingForm(ModelForm):
            name = CharField(max_length=255)

            class Meta:
                model = Defaults
                exclude = ["name", "callable_default"]

        f = ExcludingForm(
            {"name": "Hello", "value": 99, "def_date": datetime.date(1999, 3, 2)}
        )
        self.assertTrue(f.is_valid())
        self.assertEqual(f.cleaned_data["name"], "Hello")
        obj = f.save()
        self.assertEqual(obj.name, "class default value")
        self.assertEqual(obj.value, 99)
        self.assertEqual(obj.def_date, datetime.date(1999, 3, 2))