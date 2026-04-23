def test_i18n32(self):
        output = self.engine.render_to_string("i18n32")
        self.assertEqual(output, "Hungarian Magyar False Hungarian")

        with translation.override("cs"):
            output = self.engine.render_to_string("i18n32")
            self.assertEqual(output, "Hungarian Magyar False maďarsky")