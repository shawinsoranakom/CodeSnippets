def test_in_memory_spooled_temp(self):
        with tempfile.SpooledTemporaryFile() as temp:
            temp.write(b"foo bar baz quux\n")
            django_file = File(temp, name="something.txt")
            self.assertEqual(django_file.size, 17)