def test_io_wrapper(self):
        content = "vive l'été\n"
        with (
            tempfile.TemporaryFile() as temp,
            File(temp, name="something.txt") as test_file,
        ):
            test_file.write(content.encode())
            test_file.seek(0)
            wrapper = TextIOWrapper(test_file, "utf-8", newline="\n")
            self.assertEqual(wrapper.read(), content)
            wrapper.write(content)
            wrapper.seek(0)
            self.assertEqual(wrapper.read(), content * 2)
            test_file = wrapper.detach()
            test_file.seek(0)
            self.assertEqual(test_file.read(), (content * 2).encode())