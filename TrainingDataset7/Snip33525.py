def test_script(self):
        output = self.engine.render_to_string("script", {"frag": "<script>"})
        self.assertTrue(
            output.startswith("{&#x27;frag&#x27;: &#x27;&lt;script&gt;&#x27;}")
        )