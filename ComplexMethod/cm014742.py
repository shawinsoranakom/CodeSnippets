def test_CTCLoss_no_batch_dim(self, device, reduction, use_module_form):
        input_length = 40
        vocab_size = 3
        target_length = 12

        args = self._CTCLoss_gen_losses(device, input_length, vocab_size, target_length, reduction, use_module_form)
        losses, losses_no_bd, log_probs_refs, log_probs_no_bd_refs = args

        # test output values
        self._assertEqual_list(losses[0], losses[1:], atol=1e-4, rtol=0)
        self._assertEqual_list(losses[0].squeeze(0), losses_no_bd, atol=1e-4, rtol=0)

        # test gradient values
        self._assertEqual_list(log_probs_refs[0].grad, [t.grad for t in log_probs_refs[1:]], atol=1e-4, rtol=0)
        self._assertEqual_list(
            log_probs_refs[0].grad.squeeze(1),
            [t.grad for t in log_probs_no_bd_refs],
            atol=1e-4,
            rtol=0,
        )

        # checking the output's shape
        # batch dim case should be (N,). no batch dim case should be ()
        self._assertEqual_list((1,) if reduction == 'none' else (), [loss.shape for loss in losses])
        self._assertEqual_list((), [loss.shape for loss in losses_no_bd])

        # checking the gradient's shape
        # batch dim case should have shape (T, N, C). no batch dim case should have shape (T, C)
        self._assertEqual_list((input_length, 1, vocab_size), [t.grad.shape for t in log_probs_refs])
        self._assertEqual_list((input_length, vocab_size), [t.grad.shape for t in log_probs_no_bd_refs])