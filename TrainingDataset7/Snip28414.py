def test_show_hidden_initial_changed_queries_efficiently(self):
        class WriterForm(forms.Form):
            persons = forms.ModelMultipleChoiceField(
                show_hidden_initial=True, queryset=Writer.objects.all()
            )

        writers = (Writer.objects.create(name=str(x)) for x in range(0, 50))
        writer_pks = tuple(x.pk for x in writers)
        form = WriterForm(data={"initial-persons": writer_pks})
        with self.assertNumQueries(1):
            self.assertTrue(form.has_changed())