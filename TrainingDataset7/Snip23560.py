def test_fetch_mode_copied_forward_fetching_many(self):
        tags = list(TaggedItem.objects.fetch_mode(FETCH_PEERS).order_by("tag"))
        tag = [t for t in tags if t.tag == "yellow"][0]
        self.assertEqual(tag.content_object, self.lion)
        self.assertEqual(
            tag.content_object._state.fetch_mode,
            FETCH_PEERS,
        )