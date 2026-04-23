def to(g: jit_utils.GraphContext, self, *args):
    def is_aten_to_device_only(args):
        if len(args) == 4:
            # aten::to(Tensor, Device, bool, bool, memory_format)
            return (
                args[0].node().kind() == "prim::device"
                or args[0].type().isSubtypeOf(_C.ListType.ofInts())
                or isinstance(args[0].type(), _C.DeviceObjType)
            )
        elif len(args) == 5:
            # aten::to(Tensor, Device, ScalarType, bool, bool, memory_format)
            # When dtype is None, this is a aten::to(device) call
            dtype = symbolic_helper._get_const(args[1], "i", "dtype")
            return dtype is None
        elif len(args) in (6, 7):
            # aten::to(Tensor, ScalarType, Layout, Device, bool, bool, memory_format) -> Tensor
            # aten::to(Tensor, ScalarType, Layout, Device, bool, bool, bool, memory_format) -> Tensor
            # When dtype is None, this is a aten::to(device) call
            dtype = symbolic_helper._get_const(args[0], "i", "dtype")
            return dtype is None
        return False

    # ONNX doesn't have a concept of a device, so we ignore device-only casts
    if is_aten_to_device_only(args):
        return self

    if len(args) == 4:
        # TestONNXRuntime::test_ones_bool shows args[0] of aten::to() can be onnx::Constant[value=<Tensor>]()
        # In this case, the constant value is a tensor not int,
        # so symbolic_helper._maybe_get_const(args[0], 'i') would not work.
        dtype = args[0]
        if (
            symbolic_helper._is_value(args[0])
            and args[0].node().kind() == "onnx::Constant"
        ):
            tval = symbolic_helper._node_get(args[0].node(), "value")
            if isinstance(tval, torch.Tensor):
                if len(tval.shape) == 0:
                    tval = tval.item()
                    dtype = int(tval)
                else:
                    dtype = tval

        if symbolic_helper._is_value(dtype) or isinstance(dtype, torch.Tensor):
            # aten::to(Tensor, Tensor, bool, bool, memory_format)
            dtype = _type_utils.JitScalarType.from_value(args[0])
            return g.op(
                "Cast",
                self,
                to_i=dtype.onnx_type(),
            )
        else:
            # aten::to(Tensor, ScalarType, bool, bool, memory_format)
            # memory_format is ignored
            return g.op("Cast", self, to_i=_type_utils.JitScalarType(dtype).onnx_type())
    elif len(args) == 5:
        # aten::to(Tensor, Device, ScalarType, bool, bool, memory_format)
        dtype = symbolic_helper._get_const(args[1], "i", "dtype")
        # memory_format is ignored
        return g.op("Cast", self, to_i=_type_utils.JitScalarType(dtype).onnx_type())
    elif len(args) == 6:
        # aten::to(Tensor, ScalarType, Layout, Device, bool, bool, memory_format) -> Tensor
        dtype = symbolic_helper._get_const(args[0], "i", "dtype")
        # Layout, device and memory_format are ignored
        return g.op("Cast", self, to_i=_type_utils.JitScalarType(dtype).onnx_type())
    elif len(args) == 7:
        # aten::to(Tensor, ScalarType, Layout, Device, bool, bool, bool, memory_format) -> Tensor
        dtype = symbolic_helper._get_const(args[0], "i", "dtype")
        # Layout, device and memory_format are ignored
        return g.op("Cast", self, to_i=_type_utils.JitScalarType(dtype).onnx_type())

    return symbolic_helper._onnx_unsupported("Unknown aten::to signature", self)