def test_defer_annotate_select_related(self):
        location = Location.objects.create()
        Request.objects.create(location=location)
        self.assertIsInstance(
            list(
                Request.objects.annotate(Count("items"))
                .select_related("profile", "location")
                .only("profile", "location")
            ),
            list,
        )
        self.assertIsInstance(
            list(
                Request.objects.annotate(Count("items"))
                .select_related("profile", "location")
                .only("profile__profile1", "location__location1")
            ),
            list,
        )
        self.assertIsInstance(
            list(
                Request.objects.annotate(Count("items"))
                .select_related("profile", "location")
                .defer("request1", "request2", "request3", "request4")
            ),
            list,
        )