def test_limit_choices_to_m2m_through(self):
        class DiceForm(forms.ModelForm):
            class Meta:
                model = Dice
                fields = ["numbers"]

        Number.objects.create(value=0)
        n1 = Number.objects.create(value=1)
        n2 = Number.objects.create(value=2)

        form = DiceForm()
        self.assertCountEqual(form.fields["numbers"].queryset, [n1, n2])