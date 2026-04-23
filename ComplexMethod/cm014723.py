def test_requires_grad_(self):
        m = _create_basic_net()[-1]
        if len(list(m.buffers())) <= 0:
            raise AssertionError('invalid test: expected buffers')
        if not all(not b.requires_grad for b in m.buffers()):
            raise AssertionError('invalid test: buffers should not require grad')
        if len(list(m.parameters())) <= 0:
            raise AssertionError('invalid test: expected parameters')
        if not all(p.requires_grad for p in m.parameters()):
            raise AssertionError('invalid test: parameters should require grad')
        for requires_grad in (False, True):
            self.assertIs(m.requires_grad_(requires_grad), m)
            for p in m.parameters():
                self.assertEqual(p.requires_grad, requires_grad)
            for b in m.buffers():
                self.assertFalse(b.requires_grad)