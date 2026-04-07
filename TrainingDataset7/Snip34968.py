def test_pdb_with_parallel(self):
        msg = "You cannot use --pdb with parallel tests; pass --parallel=1 to use it."
        with self.assertRaisesMessage(ValueError, msg):
            DiscoverRunner(pdb=True, parallel=2)