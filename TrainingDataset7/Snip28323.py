def test_blank_false_with_null_true_foreign_key_field(self):
        """
        A ModelForm with a model having ForeignKey(blank=False, null=True)
        and the form field set to required=False should allow the field to be
        unset.
        """

        class AwardForm(forms.ModelForm):
            class Meta:
                model = Award
                fields = "__all__"

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.fields["character"].required = False

        character = Character.objects.create(
            username="user", last_action=datetime.datetime.today()
        )
        award = Award.objects.create(name="Best sprinter", character=character)
        data = {"name": "Best tester", "character": ""}  # remove character
        form = AwardForm(data=data, instance=award)
        self.assertTrue(form.is_valid())
        award = form.save()
        self.assertIsNone(award.character)