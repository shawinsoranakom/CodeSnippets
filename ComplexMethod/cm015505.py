def _verify_parity(self, losses, outputs, models):
        if not losses:
            raise AssertionError("Expected losses to be non-empty")
        if not outputs:
            raise AssertionError("Expected outputs to be non-empty")
        if not models:
            raise AssertionError("Expected models to be non-empty")
        for l, o in zip(losses[1:], outputs[1:]):
            self.assertEqual(losses[0], l)
            self.assertEqual(outputs[0], o)
        # Verify grads
        ref_model = models[0]
        ref_grads = [p.grad for p in ref_model.parameters()]
        for m in models[1:]:
            grads = [p.grad for p in m.parameters()]
            for ref_g, g in zip(ref_grads, grads):
                self.assertEqual(ref_g, g)