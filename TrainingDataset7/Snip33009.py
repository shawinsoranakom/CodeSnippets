def test_linenumbers2(self):
        self.assertEqual(
            linenumbers("\n".join(["x"] * 10)),
            "01. x\n02. x\n03. x\n04. x\n05. x\n06. x\n07. x\n08. x\n09. x\n10. x",
        )