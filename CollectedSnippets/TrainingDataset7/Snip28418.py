def test_modelform_subclassed_model(self):
        class BetterWriterForm(forms.ModelForm):
            class Meta:
                # BetterWriter model is a subclass of Writer with an additional
                # `score` field.
                model = BetterWriter
                fields = "__all__"

        bw = BetterWriter.objects.create(name="Joe Better", score=10)
        self.assertEqual(
            sorted(model_to_dict(bw)), ["id", "name", "score", "writer_ptr"]
        )
        self.assertEqual(sorted(model_to_dict(bw, fields=[])), [])
        self.assertEqual(
            sorted(model_to_dict(bw, fields=["id", "name"])), ["id", "name"]
        )
        self.assertEqual(
            sorted(model_to_dict(bw, exclude=[])), ["id", "name", "score", "writer_ptr"]
        )
        self.assertEqual(
            sorted(model_to_dict(bw, exclude=["id", "name"])), ["score", "writer_ptr"]
        )

        form = BetterWriterForm({"name": "Some Name", "score": 12})
        self.assertTrue(form.is_valid())
        bw2 = form.save()
        self.assertEqual(bw2.score, 12)