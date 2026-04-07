def test_fetch_mode_copied_forward_fetching_one(self):
        tag = TaggedItem.objects.fetch_mode(FETCH_PEERS).get(tag="yellow")
        self.assertEqual(tag.content_object, self.lion)
        self.assertEqual(
            tag.content_object._state.fetch_mode,
            FETCH_PEERS,
        )