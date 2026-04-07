def test_non_ascii(self):
        group = Group(name="清風")
        output = self.engine.render_to_string("non_ascii", {"group": group})
        self.assertTrue(output.startswith("{&#x27;group&#x27;: &lt;Group: 清風&gt;}"))