def test_get_renderer(self):
        with self.assertRaisesMessage(
            NotImplementedError, "subclasses must implement get_template()"
        ):
            BaseRenderer().get_template("")