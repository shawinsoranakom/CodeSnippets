def test_native_dropout_corner_case(self):
        if TEST_CUDA:
            device = "cuda"
        elif TEST_PRIVATEUSE1:
            device = torch._C._get_privateuse1_backend_name()
        for train in [True, False]:
            for p in [0.0, 1.0]:
                for current_device in [device, "cpu"]:
                    x = torch.randn(5).to(device=current_device).requires_grad_()
                    x_ref = x.detach().requires_grad_()
                    o = torch.native_dropout(x, p, train)[0]
                    o_ref = torch.dropout(x_ref, p, train)
                    o.sum().backward()
                    o_ref.sum().backward()
                    if not o.equal(o_ref):
                        raise AssertionError("Expected o.equal(o_ref) to be True")
                    if not x.grad.equal(x_ref.grad):
                        raise AssertionError(
                            "Expected x.grad.equal(x_ref.grad) to be True"
                        )