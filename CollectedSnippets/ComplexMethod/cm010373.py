def is_int_mm(op, output_dtype, args):
    return (
        op is torch.ops.aten.mm.default
        and output_dtype == torch.int32
        and len(args) == 2
        and args[0].dtype == torch.int8
        and args[1].dtype == torch.int8
        and (args[0].is_cuda or args[0].is_xpu)
        and (args[1].is_cuda or args[1].is_xpu)
    )