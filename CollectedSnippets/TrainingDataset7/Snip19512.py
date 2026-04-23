def test_printing_model_error(self):
        e = Error("Error", obj=SimpleModel)
        expected = "check_framework.SimpleModel: Error"
        self.assertEqual(str(e), expected)