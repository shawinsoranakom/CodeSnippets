def _test_tp_backward_impl(rank, model_path, model_class, atol, rtol):
    """Implementation for comparing TP and non-TP model backward passes."""
    set_seed(0)

    model_tp, model, device = _load_tp_and_reference_models(model_path, model_class)
    model_tp.train()
    model.train()

    vocab_size = model.config.vocab_size
    set_seed(0)
    input_ids = torch.randint(0, vocab_size, (2, 64)).to(device)
    set_seed(0)
    labels = torch.randint(0, vocab_size, (2, 64)).to(device)

    loss = model(input_ids, labels=labels).loss
    loss.backward()

    loss_tp = model_tp(input_ids, labels=labels).loss
    loss_tp.backward()

    assert torch.allclose(loss, loss_tp, atol=atol, rtol=rtol), (
        f"TP and non-TP model losses differ. "
        f"Non-TP loss: {loss.item()}, TP loss: {loss_tp.item()}, "
        f"Diff: {(loss - loss_tp).abs().item()}"
    )

    # Compare gradients for matching parameters
    world_size = dist.get_world_size()
    failed_grads = {}
    for (name, param), (_, param_tp) in zip(model.named_parameters(), model_tp.named_parameters()):
        if param.grad is not None and param_tp.grad is not None:
            grad = param.grad
            grad_tp = param_tp.grad

            # Slice reference gradient to match local shard if parameter is sharded
            if grad.shape != grad_tp.shape:
                for dim in range(grad.ndim):
                    if grad.size(dim) != grad_tp.size(dim):
                        param_plan = _get_parameter_tp_plan(name, model_tp.tp_plan, is_weight=True)
                        if param_plan in ("packed_colwise",):
                            # interleaved slicing
                            grad = get_packed_grad_shard(grad, world_size, rank, dim)
                        else:
                            # regular slicing
                            shard_size = grad_tp.size(dim)
                            start = rank * shard_size
                            grad = grad.narrow(dim, start, shard_size)
                        break

            if not torch.allclose(grad.cpu(), grad_tp.cpu(), atol=atol, rtol=rtol):
                failed_grads[name] = (grad.cpu() - grad_tp.cpu()).abs().max().item()

    assert not failed_grads, f"Gradients differ for {len(failed_grads)} parameter(s):\n" + "\n".join(
        f"  {name}: max diff = {diff}" for name, diff in failed_grads.items()
    )

    dist.barrier()