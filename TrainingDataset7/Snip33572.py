def test_inheritance41(self):
        output = self.engine.render_to_string("inheritance41", {"numbers": "123"})
        self.assertEqual(output, "_new1_new2_new3_")