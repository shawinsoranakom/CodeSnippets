def test_partial_defined_outside_main_block(self):
        output = self.engine.render_to_string("partial_with_extends")
        self.assertIn("<main>Main content with Inside Content</main>", output)