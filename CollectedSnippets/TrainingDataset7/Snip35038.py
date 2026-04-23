def test_shuffle_same_hash(self):
        shuffler = Shuffler(seed=1234)
        msg = "item 'A' has same hash 'a56ce89262959e151ee2266552f1819c' as item 'a'"
        with self.assertRaisesMessage(RuntimeError, msg):
            shuffler.shuffle(["a", "b", "A"], lambda x: x.upper())