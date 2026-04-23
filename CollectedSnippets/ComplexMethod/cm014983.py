def test_functional_call_member_reference(self, functional_call):
        class Module(torch.nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.l1 = torch.nn.Linear(1, 1)
                self.buffer = torch.nn.Buffer(torch.ones(1))

            def forward(self, x):
                parameters = tuple(self.parameters())
                buffers = tuple(self.buffers())
                return self.l1(x) + self.buffer, parameters, buffers

        module = Module()
        weight = torch.tensor([[2.0]])
        bias = torch.tensor([5.0])
        buffer = torch.tensor([3.0])
        extra = torch.tensor([1.0])
        extra_p = torch.nn.Parameter(extra)

        # All weights
        parameters = {'l1.weight': weight,
                      'l1.bias': bias,
                      'buffer': buffer}
        x = torch.randn(1, 1)
        out, parameters, buffers = functional_call(module, parameters, x)
        self.assertEqual(out, x * weight + bias + buffer)
        self.assertEqual(parameters, (weight, bias))
        self.assertEqual(buffers, (buffer,))
        self.assertTrue(all(t1 is t2 for t1, t2 in zip(parameters, (weight, bias))))
        self.assertTrue(all(t1 is t2 for t1, t2 in zip(buffers, (buffer,))))

        # Some weights
        parameters = {'l1.weight': weight}
        x = torch.randn(1, 1)
        out, parameters, buffers = functional_call(module, parameters, x)
        self.assertEqual(out, x * weight + module.l1.bias + module.buffer)
        self.assertEqual(parameters, (weight, module.l1.bias))
        self.assertEqual(buffers, (module.buffer,))
        self.assertTrue(all(t1 is t2 for t1, t2 in zip(parameters, (weight, module.l1.bias))))
        self.assertTrue(all(t1 is t2 for t1, t2 in zip(buffers, (module.buffer,))))

        # All weights with extra keys
        parameters = {'l1.weight': weight,
                      'l1.bias': bias,
                      'buffer': buffer,
                      'l1.extra': extra}
        x = torch.randn(1, 1)
        out, parameters, buffers = functional_call(module, parameters, x)
        self.assertEqual(out, x * weight + bias + buffer)
        self.assertEqual(parameters, (weight, bias))
        self.assertEqual(buffers, (buffer,))
        self.assertTrue(all(t1 is t2 for t1, t2 in zip(parameters, (weight, bias))))
        self.assertTrue(all(t1 is t2 for t1, t2 in zip(buffers, (buffer,))))

        # All weights with extra keys with parameters
        parameters = {'l1.weight': weight,
                      'l1.bias': bias,
                      'buffer': buffer,
                      'l1.extra': extra_p}
        x = torch.randn(1, 1)
        out, parameters, buffers = functional_call(module, parameters, x)
        self.assertEqual(out, x * weight + bias + buffer)
        self.assertEqual(parameters, (weight, bias, extra_p))
        self.assertEqual(buffers, (buffer,))
        self.assertTrue(all(t1 is t2 for t1, t2 in zip(parameters, (weight, bias, extra_p))))
        self.assertTrue(all(t1 is t2 for t1, t2 in zip(buffers, (buffer,))))

        # Some weights with extra keys
        parameters = {'l1.weight': weight,
                      'l1.extra': extra}
        x = torch.randn(1, 1)
        out, parameters, buffers = functional_call(module, parameters, x)
        self.assertEqual(out, x * weight + module.l1.bias + module.buffer)
        self.assertEqual(parameters, (weight, module.l1.bias))
        self.assertEqual(buffers, (module.buffer))
        self.assertTrue(all(t1 is t2 for t1, t2 in zip(parameters, (weight, module.l1.bias))))
        self.assertTrue(all(t1 is t2 for t1, t2 in zip(buffers, (module.buffer,))))

        # Some weights with extra keys with parameters
        parameters = {'l1.weight': weight,
                      'l1.extra': extra_p}
        x = torch.randn(1, 1)
        out, parameters, buffers = functional_call(module, parameters, x)
        self.assertEqual(out, x * weight + module.l1.bias + module.buffer)
        self.assertEqual(parameters, (weight, module.l1.bias, extra_p))
        self.assertEqual(buffers, (module.buffer))
        self.assertTrue(all(t1 is t2 for t1, t2 in zip(parameters, (weight, module.l1.bias, extra_p))))
        self.assertTrue(all(t1 is t2 for t1, t2 in zip(buffers, (module.buffer,))))

        # Set None
        parameters = {'l1.weight': weight,
                      'l1.bias': None}
        x = torch.randn(1, 1)
        out, parameters, buffers = functional_call(module, parameters, x)
        self.assertEqual(out, x * weight + module.buffer)
        self.assertEqual(parameters, (weight,))
        self.assertEqual(buffers, (module.buffer))
        self.assertTrue(all(t1 is t2 for t1, t2 in zip(parameters, (weight,))))
        self.assertTrue(all(t1 is t2 for t1, t2 in zip(buffers, (module.buffer,))))