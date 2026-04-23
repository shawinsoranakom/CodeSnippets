def test_hash_text_hash_algorithm(self):
        class MyShuffler(Shuffler):
            hash_algorithm = "sha1"

        actual = MyShuffler._hash_text("abcd")
        self.assertEqual(actual, "81fe8bfe87576c3ecb22426f8e57847382917acf")