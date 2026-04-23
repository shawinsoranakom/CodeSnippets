def test_m2m_through_gfk(self):
        TaggedItem.objects.create(tag="houses", content_object=self.house1)
        TaggedItem.objects.create(tag="houses", content_object=self.house2)

        # Control lookups.
        with self.assertNumQueries(3):
            lst1 = self.traverse_qs(
                TaggedItem.objects.filter(tag="houses").prefetch_related(
                    "content_object__rooms"
                ),
                [["content_object", "rooms"]],
            )

        # Test lookups.
        with self.assertNumQueries(3):
            lst2 = self.traverse_qs(
                TaggedItem.objects.prefetch_related(
                    Prefetch("content_object"),
                    Prefetch("content_object__rooms", to_attr="rooms_lst"),
                ),
                [["content_object", "rooms_lst"]],
            )
        self.assertEqual(lst1, lst2)