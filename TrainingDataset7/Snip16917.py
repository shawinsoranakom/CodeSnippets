def test_filtered_reused_subquery(self):
        qs = Author.objects.annotate(
            older_friends_count=Count("friends", filter=Q(friends__age__gt=F("age"))),
        ).filter(
            older_friends_count__gte=2,
        )
        self.assertEqual(qs.get(pk__in=qs.values("pk")), self.a1)