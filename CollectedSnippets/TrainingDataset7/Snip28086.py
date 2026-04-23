def test_json_type_casting_with_coalesce(self):
        RelatedJSONModel.objects.create(
            summary='"This is valid JSON primitive."',
            value={"text": "test"},
            json_model=self.objs[4],
        )
        result = RelatedJSONModel.objects.annotate(
            coalesced_value=Coalesce(
                Cast("summary", JSONField()), "value", output_field=JSONField()
            )
        ).first()
        self.assertEqual(result.coalesced_value, "This is valid JSON primitive.")