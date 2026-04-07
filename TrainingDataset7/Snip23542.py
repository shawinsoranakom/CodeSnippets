def test_query_content_type(self):
        msg = "Field 'content_object' does not generate an automatic reverse relation"
        with self.assertRaisesMessage(FieldError, msg):
            TaggedItem.objects.get(content_object="")