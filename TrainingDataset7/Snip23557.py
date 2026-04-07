def test_fetch_mode_fetch_peers(self):
        TaggedItem.objects.bulk_create(
            [
                TaggedItem(tag="lion", content_object=self.lion),
                TaggedItem(tag="platypus", content_object=self.platypus),
                TaggedItem(tag="quartz", content_object=self.quartz),
            ]
        )
        # Peers fetching should fetch all related peers GFKs at once which is
        # one query per content type.
        with self.assertNumQueries(1):
            quartz_tag, platypus_tag, lion_tag = TaggedItem.objects.fetch_mode(
                FETCH_PEERS
            ).order_by("-pk")[:3]
        with self.assertNumQueries(2):
            self.assertEqual(lion_tag.content_object, self.lion)
        with self.assertNumQueries(0):
            self.assertEqual(platypus_tag.content_object, self.platypus)
            self.assertEqual(quartz_tag.content_object, self.quartz)
        # It should ignore already cached instances though.
        with self.assertNumQueries(1):
            quartz_tag, platypus_tag, lion_tag = TaggedItem.objects.fetch_mode(
                FETCH_PEERS
            ).order_by("-pk")[:3]
        with self.assertNumQueries(2):
            self.assertEqual(quartz_tag.content_object, self.quartz)
            self.assertEqual(lion_tag.content_object, self.lion)
        with self.assertNumQueries(0):
            self.assertEqual(platypus_tag.content_object, self.platypus)
            self.assertEqual(quartz_tag.content_object, self.quartz)