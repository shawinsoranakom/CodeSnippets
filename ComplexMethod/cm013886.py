def collect_results(
    model: torch.nn.Module, prediction: Any, loss: Any, example_inputs: Any
) -> list[Any]:
    results = []
    results.append(prediction)
    results.append(loss)
    # if isinstance(loss, torch.Tensor) and loss.item() > 1:
    #     log.warning(
    #         f"High loss value alert - {loss:.2f}. Can result in unstable gradients."
    #     )

    grads = {}
    params = {}
    for name, param in model.named_parameters():
        if isinstance(model, eval_frame.OptimizedModule):
            name = remove_optimized_module_prefix(name)
        param_copy = param
        grad = param.grad
        # Treat None and zero grad as same
        if param.grad is None:
            grad = torch.zeros_like(param)
        grads[name + ".grad"] = grad
        params[name] = param_copy
    results.append(grads)
    results.append(params)
    buffers = {}
    for name, buffer in model.named_buffers():
        if isinstance(model, eval_frame.OptimizedModule):
            name = remove_optimized_module_prefix(name)
        buffers[name] = buffer
    results.append(buffers)
    for example in example_inputs:
        if isinstance(example, (tuple, list)):
            results.extend(inp.grad for inp in example if isinstance(inp, torch.Tensor))
        else:
            if isinstance(example, torch.Tensor):
                results.append(example.grad)
    return results