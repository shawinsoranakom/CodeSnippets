def test_non_blank_foreign_key_with_radio(self):
        class AwardForm(forms.ModelForm):
            class Meta:
                model = Award
                fields = ["character"]
                widgets = {"character": forms.RadioSelect()}

        character = Character.objects.create(
            username="user",
            last_action=datetime.datetime.today(),
        )
        form = AwardForm()
        self.assertEqual(
            list(form.fields["character"].choices),
            [(character.pk, "user")],
        )