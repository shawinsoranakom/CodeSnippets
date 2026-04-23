def test_torch_tensor(self):
        a = torch.ones([1, 1])
        b = torch.ones([1, 1], requires_grad=True)
        c = torch.ones([1, 2])

        self.assertEqual(get_hash(a), get_hash(b))
        self.assertNotEqual(get_hash(a), get_hash(c))

        b.mean().backward()

        self.assertNotEqual(get_hash(a), get_hash(b))