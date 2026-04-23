def test_rnn_pruning(self):
        l = torch.nn.LSTM(32, 32)
        # This Module has 4 parameters called:
        # 'weight_ih_l0', 'weight_hh_l0', 'bias_ih_l0', 'bias_hh_l0'

        # Pruning one of them causes one of the weights to become a tensor
        prune.l1_unstructured(l, "weight_ih_l0", 0.5)
        param_count = sum(isinstance(p, torch.nn.Parameter) for p in l._flat_weights)
        if param_count != 3:
            raise AssertionError(
                f"Expected 3 Parameters in _flat_weights after pruning, got {param_count}"
            )

        # Removing the pruning reparameterization restores the Parameter
        prune.remove(l, "weight_ih_l0")
        param_count = sum(isinstance(p, torch.nn.Parameter) for p in l._flat_weights)
        if param_count != 4:
            raise AssertionError(
                f"Expected 4 Parameters in _flat_weights after removal, got {param_count}"
            )

        # Make sure that, upon removal of the reparameterization, the
        # `._parameters` and `.named_parameters` contain the right params.
        # Specifically, the original weight ('weight_ih_l0') should be placed
        # back in the parameters, while the reparameterization component
        # ('weight_ih_l0_orig') should be removed.
        if "weight_ih_l0" not in l._parameters:
            raise AssertionError("'weight_ih_l0' should be in l._parameters")
        if l._parameters["weight_ih_l0"] is None:
            raise AssertionError("l._parameters['weight_ih_l0'] should not be None")
        if "weight_ih_l0_orig" in l._parameters:
            raise AssertionError("'weight_ih_l0_orig' should not be in l._parameters")
        if "weight_ih_l0" not in dict(l.named_parameters()):
            raise AssertionError("'weight_ih_l0' should be in l.named_parameters()")
        if dict(l.named_parameters())["weight_ih_l0"] is None:
            raise AssertionError(
                "l.named_parameters()['weight_ih_l0'] should not be None"
            )
        if "weight_ih_l0_orig" in dict(l.named_parameters()):
            raise AssertionError(
                "'weight_ih_l0_orig' should not be in l.named_parameters()"
            )