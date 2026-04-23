def _CTCLoss_gen_losses(self, device, input_length, vocab_size, target_length, reduction, use_module_form):
        batch_size = 1
        log_probs = torch.randn(input_length, batch_size, vocab_size, dtype=torch.float, device=device) \
                         .log_softmax(2).requires_grad_()
        targets = torch.randint(low=1, high=vocab_size - 1, size=(batch_size, target_length),
                                dtype=torch.int, device=device)
        input_lengths = batch_size * [input_length]
        target_lengths = batch_size * [target_length]

        log_probs_no_bd = log_probs.squeeze(1).detach().clone().requires_grad_()
        targets_no_bd = targets.squeeze(0).detach().clone()
        input_lengths_no_bd = torch.tensor(input_length)
        target_lengths_no_bd = torch.tensor(target_length)

        # currently only length 2 and 1 right now, but left flexible for additional potential cases
        log_probs_refs = [log_probs.detach().clone().requires_grad_() for _ in range(2)]
        log_probs_no_bd_refs = [log_probs_no_bd.detach().clone().requires_grad_() for _ in range(1)]

        losses = []
        losses_no_bd = []

        has_cuda = torch.cuda.is_available()
        has_cudnn = has_cuda and 'cuda' in device and self.has_cudnn()
        # cudnn requires a cpu target
        if has_cuda and has_cudnn:
            targets = targets.cpu()
            targets_no_bd = targets_no_bd.cpu()

        ctc_loss = (
            nn.CTCLoss(reduction=reduction, zero_infinity=True)
            if use_module_form
            else partial(torch.nn.functional.ctc_loss, reduction=reduction, zero_infinity=True)
        )

        with torch.backends.cudnn.flags(enabled=has_cudnn):
            # batched case. log_probs.shape = (T, N, C), targets = (N, S), input_lengths/target_lengths = (N,)
            losses.append(ctc_loss(log_probs_refs[0], targets, input_lengths, target_lengths))
            # batched case. input.shape = (T, N, C), targets = (S,), input_lengths/target_lengths = (N,)
            losses.append(ctc_loss(log_probs_refs[1], targets_no_bd, input_lengths, target_lengths))
            # unbatched case. input.shape = (T, C), targets = (S,), input_lengths/target_lengths = (N,)
            losses_no_bd.append(ctc_loss(log_probs_no_bd_refs[0], targets_no_bd,
                                         input_lengths_no_bd, target_lengths_no_bd))

            for loss in losses + losses_no_bd:
                loss.backward()

        return losses, losses_no_bd, log_probs_refs, log_probs_no_bd_refs