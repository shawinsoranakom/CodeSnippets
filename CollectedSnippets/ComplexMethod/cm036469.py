def test_registration_overloads():
    assert all(
        n not in IrOp.registry for n in ["_custom_sub", "_custom_mul", "_custom_div"]
    )

    # Calling with decorator
    @vllm.ir.register_op()
    def _custom_sub(x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        return x - y

    assert _custom_sub.name == "_custom_sub"
    assert _custom_sub is IrOp.registry["_custom_sub"]

    # Custom name
    @vllm.ir.register_op(name="_custom_mul")
    def custom_mul(x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        return x * y

    assert custom_mul.name == "_custom_mul"
    assert custom_mul is IrOp.registry["_custom_mul"]

    # Direct construction does not register directly
    def _custom_div(x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        return x / y

    custom_div = IrOp("_custom_div", _custom_div)
    assert custom_div.name == "_custom_div"
    assert "_custom_div" not in IrOp.registry

    # Duplicate op registration not allowed
    with pytest.raises(AssertionError):

        @vllm.ir.register_op
        def _custom_mul(x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
            return x * y - 100