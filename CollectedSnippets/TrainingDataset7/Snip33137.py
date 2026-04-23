def test_unicode(self):
        self.assertEqual(title("discoth\xe8que"), "Discoth\xe8que")