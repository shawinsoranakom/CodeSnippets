def test_ctc_loss(self, device):
        batch_size = 64
        num_labels = 101
        target_length = 15
        gradcheck_input_size = 10

        ZERO_NONE = 0
        ZERO_SOME = 1
        ZERO_ALL = 2

        # input_length, vary_lengths, zero_lengths
        tests = [(150, False, ZERO_NONE),
                 (150, True, ZERO_NONE),
                 (50, True, ZERO_SOME),
                 (50, True, ZERO_ALL)]

        if 'cuda' in device:
            tests += [(50, False, ZERO_NONE),
                      (50, True, ZERO_NONE),
                      (150, True, ZERO_SOME),
                      (150, True, ZERO_ALL)]

        for input_length, vary_lengths, zero_mode in tests:
            targets = torch.randint(1, num_labels, (batch_size, target_length),
                                    device=device, dtype=torch.long)
            x = torch.randn(gradcheck_input_size, dtype=torch.double, device=device, requires_grad=True)
            tile_factors = torch.randn(input_length * batch_size * num_labels // gradcheck_input_size + 1,
                                       device=device)
            input_lengths = [(torch.randint(input_length // 2, input_length + 1, ()).item()
                              if vary_lengths or i == 0 else input_length) for i in range(batch_size)]
            if zero_mode == ZERO_ALL:
                target_lengths = [0 for _ in range(batch_size)]
            else:
                target_lengths = [(torch.randint(target_length // 2, target_length + 1, ()).item()
                                   if vary_lengths else target_length) for _ in range(batch_size)]
                if zero_mode == ZERO_SOME:
                    idxes = torch.randint(0, batch_size, (10,))
                    for i in idxes:
                        target_lengths[i] = 0

            def ctc_after_softmax(x):
                x_full = ((x[:, None] * tile_factors[None, :]).view(-1)[:input_length * batch_size * num_labels]
                          .view(input_length, batch_size, num_labels))
                log_probs = torch.log_softmax(x_full, 2)
                return torch.nn.functional.ctc_loss(log_probs, targets, input_lengths, target_lengths)

            gradcheck(ctc_after_softmax, [x])