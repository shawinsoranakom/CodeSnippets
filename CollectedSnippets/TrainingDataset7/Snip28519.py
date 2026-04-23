def test_deletion(self):
        PoetFormSet = modelformset_factory(Poet, fields="__all__", can_delete=True)
        poet = Poet.objects.create(name="test")
        data = {
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "1",
            "form-MAX_NUM_FORMS": "0",
            "form-0-id": str(poet.pk),
            "form-0-name": "test",
            "form-0-DELETE": "on",
        }
        formset = PoetFormSet(data, queryset=Poet.objects.all())
        formset.save(commit=False)
        self.assertEqual(Poet.objects.count(), 1)

        formset.save()
        self.assertTrue(formset.is_valid())
        self.assertEqual(Poet.objects.count(), 0)