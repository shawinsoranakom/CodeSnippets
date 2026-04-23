def test_tma_capture_and_functionalize(self, dynamic, tma_version):
        if tma_version == "new" and not has_triton_tensor_descriptor_host_tma():
            self.skipTest("requires triton.tools.tensor_descriptor TMA support")
        if tma_version == "old" and not has_triton_experimental_host_tma():
            self.skipTest("requires triton.tools.experimental_descriptor TMA support")

        from torch._higher_order_ops.triton_kernel_wrap import kernel_side_table

        kernel_side_table.reset_table()
        kernel = (
            add_kernel_with_tma_1d_new_api
            if tma_version == "new"
            else add_kernel_with_tma_1d_old_api
        )

        def f(a, b):
            BLOCK_SIZE = 256
            out = torch.zeros_like(a)
            n_elements = out.numel()

            desc_a, desc_b, desc_out = (
                create_tensor_descriptor_shim(
                    t, [BLOCK_SIZE], new_api=(tma_version == "new")
                )
                for t in (a, b, out)
            )

            grid = lambda meta: (triton.cdiv(n_elements, meta["BLOCK_SIZE"]),)
            kernel[grid](
                desc_a,
                desc_b,
                desc_out,
                BLOCK_SIZE=BLOCK_SIZE,
            )

            return out

        a = torch.randn(301, device=GPU_TYPE)
        b = torch.randn(301, device=GPU_TYPE)

        backend = torch._dynamo.testing.AotEagerAndRecordGraphs()
        _ = f(a, b)
        torch.compile(
            f,
            fullgraph=True,
            backend=backend,
            dynamic=dynamic,
        )(a, b)

        if dynamic:
            if tma_version == "new":
                self.assertExpectedInline(
                    backend.fw_graphs[0].code.strip(),
                    """\
def forward(self, arg0_1, arg1_1, arg2_1):
    zeros_like = torch.ops.aten.zeros_like.default(arg1_1, pin_memory = False)
    add_2 = arg0_1 + 256;  arg0_1 = None
    sub_1 = add_2 - 1;  add_2 = None
    floordiv = sub_1 // 256;  sub_1 = None
    triton_kernel_wrapper_functional_proxy = torch.ops.higher_order.triton_kernel_wrapper_functional(kernel_idx = 0, constant_args_idx = 0, grid = [(floordiv, 1, 1)], tma_descriptor_metadata = {'in_desc_ptr0': ('stable', ([256],)), 'in_desc_ptr1': ('stable', ([256],)), 'out_desc_ptr': ('stable', ([256],))}, kwargs = {'in_desc_ptr0': arg1_1, 'in_desc_ptr1': arg2_1, 'out_desc_ptr': zeros_like}, tensors_to_clone = ['out_desc_ptr']);  floordiv = arg1_1 = arg2_1 = zeros_like = None
    getitem = triton_kernel_wrapper_functional_proxy['out_desc_ptr'];  triton_kernel_wrapper_functional_proxy = None
    return (getitem,)""",
                )
            elif tma_version == "old":
                self.assertExpectedInline(
                    backend.fw_graphs[0].code.strip(),
                    """\
def forward(self, arg0_1, arg1_1, arg2_1):
    zeros_like = torch.ops.aten.zeros_like.default(arg1_1, pin_memory = False)
    add_2 = arg0_1 + 256
    sub_1 = add_2 - 1;  add_2 = None
    floordiv = sub_1 // 256;  sub_1 = None
    triton_kernel_wrapper_functional_proxy = torch.ops.higher_order.triton_kernel_wrapper_functional(kernel_idx = 0, constant_args_idx = 0, grid = [(floordiv, 1, 1)], tma_descriptor_metadata = {'in_desc_ptr0': ('experimental', ([arg0_1], [256], 4)), 'in_desc_ptr1': ('experimental', ([arg0_1], [256], 4)), 'out_desc_ptr': ('experimental', ([arg0_1], [256], 4))}, kwargs = {'in_desc_ptr0': arg1_1, 'in_desc_ptr1': arg2_1, 'out_desc_ptr': zeros_like}, tensors_to_clone = ['out_desc_ptr']);  floordiv = arg0_1 = arg1_1 = arg2_1 = zeros_like = None
    getitem = triton_kernel_wrapper_functional_proxy['out_desc_ptr'];  triton_kernel_wrapper_functional_proxy = None
    return (getitem,)""",
                )
        else:
            if tma_version == "new":
                self.assertExpectedInline(
                    backend.fw_graphs[0].code.strip(),
                    """\
def forward(self, arg0_1, arg1_1):
    zeros_like = torch.ops.aten.zeros_like.default(arg0_1, pin_memory = False)
    triton_kernel_wrapper_functional_proxy = torch.ops.higher_order.triton_kernel_wrapper_functional(kernel_idx = 0, constant_args_idx = 0, grid = [(2, 1, 1)], tma_descriptor_metadata = {'in_desc_ptr0': ('stable', ([256],)), 'in_desc_ptr1': ('stable', ([256],)), 'out_desc_ptr': ('stable', ([256],))}, kwargs = {'in_desc_ptr0': arg0_1, 'in_desc_ptr1': arg1_1, 'out_desc_ptr': zeros_like}, tensors_to_clone = ['out_desc_ptr']);  arg0_1 = arg1_1 = zeros_like = None
    getitem = triton_kernel_wrapper_functional_proxy['out_desc_ptr'];  triton_kernel_wrapper_functional_proxy = None
    return (getitem,)""",
                )
            elif tma_version == "old":
                self.assertExpectedInline(
                    backend.fw_graphs[0].code.strip(),
                    """\
def forward(self, arg0_1, arg1_1):
    zeros_like = torch.ops.aten.zeros_like.default(arg0_1, pin_memory = False)
    triton_kernel_wrapper_functional_proxy = torch.ops.higher_order.triton_kernel_wrapper_functional(kernel_idx = 0, constant_args_idx = 0, grid = [(2, 1, 1)], tma_descriptor_metadata = {'in_desc_ptr0': ('experimental', ([301], [256], 4)), 'in_desc_ptr1': ('experimental', ([301], [256], 4)), 'out_desc_ptr': ('experimental', ([301], [256], 4))}, kwargs = {'in_desc_ptr0': arg0_1, 'in_desc_ptr1': arg1_1, 'out_desc_ptr': zeros_like}, tensors_to_clone = ['out_desc_ptr']);  arg0_1 = arg1_1 = zeros_like = None
    getitem = triton_kernel_wrapper_functional_proxy['out_desc_ptr'];  triton_kernel_wrapper_functional_proxy = None
    return (getitem,)""",
                )