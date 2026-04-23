def test_fetch_mode_raise(self):
        tag = TaggedItem.objects.fetch_mode(RAISE).get(tag="yellow")
        msg = "Fetching of TaggedItem.content_object blocked."
        with self.assertRaisesMessage(FieldFetchBlocked, msg) as cm:
            tag.content_object
        self.assertIsNone(cm.exception.__cause__)
        self.assertTrue(cm.exception.__suppress_context__)