def test_textfield(self):
        Article.objects.create(
            title="The Title",
            text="x" * 4000,
            written=timezone.now(),
        )
        obj = Article.objects.annotate(json_object=JSONObject(text=F("text"))).first()
        self.assertEqual(obj.json_object, {"text": "x" * 4000})