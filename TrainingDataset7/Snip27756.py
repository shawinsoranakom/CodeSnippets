def test_textchoices_blank_value(self):
        class BlankStr(models.TextChoices):
            EMPTY = "", "(Empty)"
            ONE = "ONE", "One"

        self.assertEqual(BlankStr.labels, ["(Empty)", "One"])
        self.assertEqual(BlankStr.values, ["", "ONE"])
        self.assertEqual(BlankStr.names, ["EMPTY", "ONE"])