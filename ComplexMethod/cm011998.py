def realize_input(cls, x: IRNode) -> IRNode:
        if x is None:
            return NoneAsConstantBuffer()
        if isinstance(x, (Expr, sympy.logic.boolalg.Boolean, int)):
            return ShapeAsConstantBuffer(expr=x)
        if isinstance(x, Constant):
            # We need to unset fake mode, or else the torch.tensor() call will
            # turn into a FakeTensor
            with _disable_current_modes():
                return V.graph.add_tensor_constant(
                    torch.tensor(x.value, dtype=x.get_dtype(), device=x.get_device())
                )
        if isinstance(x, ConstantBuffer):
            return x
        if isinstance(x, TensorBox):
            return cls.realize_input(x.data)
        if isinstance(x, ReinterpretView):
            return ReinterpretView(
                data=cls.realize_input(x.data), layout=x.get_layout()
            )
        if isinstance(x, BaseView):
            x.realize()
            if is_storage_and_layout(x.unwrap_view()):
                try:
                    return cls.convert_to_reinterpret_view(x)
                except NotImplementedError:
                    pass
        if isinstance(x, StorageBox):
            # TODO(jansel): impose layout preference on realized buffer
            x.realize()
            return x
        if isinstance(x, (NonTensorObj, ShapeAsConstantBuffer, OpaqueMultiOutput)):
            return x
        return cls.copy_input(x)