def test_save_does_not_close_file(self):
        p = self.PersonModel(name="Joe")
        p.mugshot.save("mug", self.file1)
        with p.mugshot as f:
            # Underlying file object wasn’t closed.
            self.assertEqual(f.tell(), 0)