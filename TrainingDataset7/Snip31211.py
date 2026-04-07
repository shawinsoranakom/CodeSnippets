def test_write(self):
        r = HttpResponseBase()
        self.assertIs(r.writable(), False)

        with self.assertRaisesMessage(
            OSError, "This HttpResponseBase instance is not writable"
        ):
            r.write("asdf")
        with self.assertRaisesMessage(
            OSError, "This HttpResponseBase instance is not writable"
        ):
            r.writelines(["asdf\n", "qwer\n"])