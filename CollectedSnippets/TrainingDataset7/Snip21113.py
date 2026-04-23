def test_bulk(self):
        s = S.objects.create(r=R.objects.create())
        for i in range(2 * GET_ITERATOR_CHUNK_SIZE):
            T.objects.create(s=s)
        #   1 (select related `T` instances)
        # + 1 (select related `U` instances)
        # + 2 (delete `T` instances in batches)
        # + 1 (delete `s`)
        self.assertNumQueries(5, s.delete)
        self.assertFalse(S.objects.exists())