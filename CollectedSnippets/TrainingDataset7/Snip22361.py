def test_force_insert_false(self):
        with self.assertNumQueries(3):
            obj = SubCounter.objects.create(pk=1, value=0)
        with self.assertNumQueries(2):
            SubCounter(pk=obj.pk, value=1).save()
        obj.refresh_from_db()
        self.assertEqual(obj.value, 1)
        with self.assertNumQueries(2):
            SubCounter(pk=obj.pk, value=2).save(force_insert=False)
        obj.refresh_from_db()
        self.assertEqual(obj.value, 2)
        with self.assertNumQueries(2):
            SubCounter(pk=obj.pk, value=3).save(force_insert=())
        obj.refresh_from_db()
        self.assertEqual(obj.value, 3)