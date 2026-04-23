def test_partial_used_with_block_super(self):
        output = self.engine.render_to_string("partial_with_extends_and_block_super")
        self.assertIn(
            "<main>Default main content. Main content with Inside Content</main>",
            output,
        )