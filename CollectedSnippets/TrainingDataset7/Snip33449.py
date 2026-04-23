def test_repr(self):
        block_context = BlockContext()
        block_context.add_blocks({"content": BlockNode("content", [])})
        self.assertEqual(
            repr(block_context),
            "<BlockContext: blocks=defaultdict(<class 'list'>, "
            "{'content': [<Block Node: content. Contents: []>]})>",
        )