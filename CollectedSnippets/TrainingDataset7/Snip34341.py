def test_simple_block_tag_invalid(self):
        msg = "Invalid arguments provided to simple_block_tag"
        with self.assertRaisesMessage(ValueError, msg):
            self.library.simple_block_tag("invalid")