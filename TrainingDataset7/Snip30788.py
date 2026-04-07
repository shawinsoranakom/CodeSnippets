def test_recursive_fk_reverse(self):
        node1 = Node.objects.create(num=42)
        node2 = Node.objects.create(num=1, parent=node1)

        self.assertEqual(list(Node.objects.filter(node=node2)), [node1])