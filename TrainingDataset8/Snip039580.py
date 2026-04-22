def test_torch_c_tensorbase(self):
        a = torch.ones([1, 1]).__reduce__()[1][2]
        b = torch.ones([1, 1], requires_grad=True).__reduce__()[1][2]
        c = torch.ones([1, 2]).__reduce__()[1][2]

        assert is_type(a, "torch._C._TensorBase")
        self.assertEqual(get_hash(a), get_hash(b))
        self.assertNotEqual(get_hash(a), get_hash(c))

        b.mean().backward()
        # Calling backward on a tensorbase doesn't seem to affect the gradient
        self.assertEqual(get_hash(a), get_hash(b))