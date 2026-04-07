def test_exclude_with_circular_fk_relation(self):
        self.assertEqual(
            ObjectB.objects.exclude(objecta__objectb__name=F("name")).count(), 0
        )