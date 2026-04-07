def test_verbatim_tag01(self):
        output = self.engine.render_to_string("verbatim-tag01")
        self.assertEqual(output, "{{bare   }}")