def test_db_cascade(self):
        related_db_op = RelatedDbOptionParent.objects.create(
            p=RelatedDbOptionGrandParent.objects.create()
        )
        CascadeDbModel.objects.bulk_create(
            [
                CascadeDbModel(db_cascade=related_db_op)
                for _ in range(2 * GET_ITERATOR_CHUNK_SIZE)
            ]
        )
        with self.assertNumQueries(1):
            results = related_db_op.delete()
            self.assertEqual(results, (1, {"delete.RelatedDbOptionParent": 1}))
        self.assertFalse(CascadeDbModel.objects.exists())
        self.assertFalse(RelatedDbOptionParent.objects.exists())