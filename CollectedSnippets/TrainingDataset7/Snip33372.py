def test_repr(self):
        node = LocalizeNode(nodelist=[], use_l10n=True)
        self.assertEqual(repr(node), "<LocalizeNode>")