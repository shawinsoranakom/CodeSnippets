def test_textnode_repr(self):
        engine = Engine()
        for temptext, reprtext in [
            ("Hello, world!", "<TextNode: 'Hello, world!'>"),
            ("One\ntwo.", "<TextNode: 'One\\ntwo.'>"),
        ]:
            template = engine.from_string(temptext)
            texts = template.nodelist.get_nodes_by_type(TextNode)
            self.assertEqual(repr(texts[0]), reprtext)