def run_backward(
    model: nn.Module, grad_output: torch.Tensor, output: torch.Tensor, X: torch.Tensor
):
    output.backward(grad_output)
    assert X.grad is not None
    for name, param in model.named_parameters():
        assert param.grad is not None, f"{name} grad is None"
    if isinstance(model, Qwen3MoeSparseMoeBlock):
        gate_grad = model.gate.weight.grad
        gate_proj_grad = torch.stack(
            [expert.gate_proj.weight.grad for expert in model.experts]
        )
        up_proj_grad = torch.stack(
            [expert.up_proj.weight.grad for expert in model.experts]
        )
        down_proj_grad = torch.stack(
            [expert.down_proj.weight.grad for expert in model.experts]
        )
    elif isinstance(model, Qwen3MoeGroupedGEMMBlock):
        gate_grad = model.gate.grad
        gate_proj_grad, up_proj_grad = model.gate_up_proj.grad.chunk(2, dim = 1)
        down_proj_grad = model.down_proj.grad
    else:
        raise ValueError(f"Unsupported model type: {type(model)}")
    return BackwardResult(
        X_grad = X.grad,
        gate_grad = gate_grad,
        gate_proj_grad = gate_proj_grad,
        up_proj_grad = up_proj_grad,
        down_proj_grad = down_proj_grad,
    )