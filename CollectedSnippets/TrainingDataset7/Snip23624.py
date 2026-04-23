def test_setup_get_and_head(self):
        view_instance = SimpleView()
        self.assertFalse(hasattr(view_instance, "head"))
        view_instance.setup(self.rf.get("/"))
        self.assertTrue(hasattr(view_instance, "head"))
        self.assertEqual(view_instance.head, view_instance.get)