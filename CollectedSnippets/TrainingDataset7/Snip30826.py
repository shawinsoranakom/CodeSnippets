def test_double_exclude(self):
        self.assertEqual(
            list(NullableName.objects.filter(~~Q(name="i1"))),
            list(NullableName.objects.filter(Q(name="i1"))),
        )
        self.assertNotIn(
            "IS NOT NULL", str(NullableName.objects.filter(~~Q(name="i1")).query)
        )