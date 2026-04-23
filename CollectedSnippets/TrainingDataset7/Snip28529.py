def test_custom_save_method(self):
        class PoetForm(forms.ModelForm):
            def save(self, commit=True):
                # change the name to "Vladimir Mayakovsky" just to be a jerk.
                author = super().save(commit=False)
                author.name = "Vladimir Mayakovsky"
                if commit:
                    author.save()
                return author

        PoetFormSet = modelformset_factory(Poet, fields="__all__", form=PoetForm)

        data = {
            "form-TOTAL_FORMS": "3",  # the number of forms rendered
            "form-INITIAL_FORMS": "0",  # the number of forms with initial data
            "form-MAX_NUM_FORMS": "",  # the max number of forms
            "form-0-name": "Walt Whitman",
            "form-1-name": "Charles Baudelaire",
            "form-2-name": "",
        }

        qs = Poet.objects.all()
        formset = PoetFormSet(data=data, queryset=qs)
        self.assertTrue(formset.is_valid())

        poets = formset.save()
        self.assertEqual(len(poets), 2)
        poet1, poet2 = poets
        self.assertEqual(poet1.name, "Vladimir Mayakovsky")
        self.assertEqual(poet2.name, "Vladimir Mayakovsky")