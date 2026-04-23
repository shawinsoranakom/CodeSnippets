def test_printing_manager_error(self):
        manager = SimpleModel.manager
        e = Error("Error", obj=manager)
        expected = "check_framework.SimpleModel.manager: Error"
        self.assertEqual(str(e), expected)