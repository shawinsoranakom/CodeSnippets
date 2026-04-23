def test_blank_with_null_foreign_key_field(self):
        """
        #13776 -- ModelForm's with models having a FK set to null=False and
        required=False should be valid.
        """

        class FormForTestingIsValid(forms.ModelForm):
            class Meta:
                model = Student
                fields = "__all__"

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.fields["character"].required = False

        char = Character.objects.create(
            username="user", last_action=datetime.datetime.today()
        )
        data = {"study": "Engineering"}
        data2 = {"study": "Engineering", "character": char.pk}

        # form is valid because required=False for field 'character'
        f1 = FormForTestingIsValid(data)
        self.assertTrue(f1.is_valid())

        f2 = FormForTestingIsValid(data2)
        self.assertTrue(f2.is_valid())
        obj = f2.save()
        self.assertEqual(obj.character, char)