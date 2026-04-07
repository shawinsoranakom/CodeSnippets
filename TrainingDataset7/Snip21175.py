def test_self_reference_with_through_m2m_at_second_level(self):
        toy = Toy.objects.create(name="Paints")
        child = Child.objects.create(name="Juan")
        Book.objects.create(pagecount=500, owner=child)
        PlayedWith.objects.create(child=child, toy=toy, date=datetime.date.today())
        with self.assertNumQueries(1) as ctx:
            Book.objects.filter(
                Exists(
                    Book.objects.filter(
                        pk=OuterRef("pk"),
                        owner__toys=toy.pk,
                    ),
                )
            ).delete()

        self.assertIs(Book.objects.exists(), False)
        sql = ctx.captured_queries[0]["sql"].lower()
        if connection.features.delete_can_self_reference_subquery:
            self.assertEqual(sql.count("select"), 1)