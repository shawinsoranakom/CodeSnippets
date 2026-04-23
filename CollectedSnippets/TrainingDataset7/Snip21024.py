def test_defer_fk_attname(self):
        primary = Primary.objects.defer("related_id").get(name="p1")
        with self.assertNumQueries(1):
            self.assertEqual(primary.related_id, self.p1.related_id)