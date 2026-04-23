def test_streaming_backwards_multiple_streams(self):
        MultiplyInStream = self._make_multiply_in_stream()

        class StreamModel(torch.nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.event = torch.cuda.Event()
                self.stream0 = torch.cuda.Stream()
                self.stream1 = torch.cuda.Stream()

            def forward(self, x, x_first_use_on_ambient):
                if x_first_use_on_ambient:
                    x0 = x.clone()
                self.stream0.wait_stream(torch.cuda.current_stream())
                self.stream1.wait_stream(torch.cuda.current_stream())
                with torch.cuda.stream(self.stream0):
                    if not x_first_use_on_ambient:
                        x0 = x.clone()
                    y0 = MultiplyInStream.apply(x0, 2)
                    self.event.record(stream=torch.cuda.current_stream())

                with torch.cuda.stream(self.stream1):
                    y1 = MultiplyInStream.apply(x, 3)
                    self.stream1.wait_event(self.event)
                    return y0 + y1

        stream = torch.cuda.Stream()

        for x_first_use_on_ambient in (True, False):
            # the out_of_place=False, iters=1 case stresses if proper syncs are inserted
            # when grads are initially None and stolen by backward ops.
            for out_of_place, iters in ((True, 1), (False, 1), (False, 5)):
                with torch.cuda.stream(stream):
                    x = torch.randn(5, 5, device="cuda", requires_grad=True)
                    model = StreamModel().cuda()
                    x.register_hook(
                        lambda grad: self.assertEqual(
                            torch.cuda.current_stream(),
                            stream if x_first_use_on_ambient else model.stream0,
                        )
                    )
                    for p in model.parameters():
                        self.assertTrue(p.grad is None)
                    for _ in range(iters):
                        loss = model(x, x_first_use_on_ambient).sum()
                        if out_of_place:
                            x_grad = torch.autograd.grad((loss,), (x,))[0]
                        else:
                            loss.backward()
                # See "Stream semantics of backward passes" on https://pytorch.org/docs/stable/notes/cuda.html
                torch.cuda.current_stream().wait_stream(stream)

                if out_of_place:
                    self.assertEqual(x_grad, torch.ones_like(x) * 5 * iters)
                else:
                    self.assertEqual(x.grad, torch.ones_like(x) * 5 * iters)