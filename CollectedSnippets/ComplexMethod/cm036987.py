def test_fix_functionalization(
    model_class: torch.nn.Module, do_fusion: bool, dtype: torch.dtype
):
    torch.set_default_device("cuda")
    torch.set_default_dtype(dtype)
    torch.manual_seed(0)

    vllm_config = VllmConfig(
        model_config=ModelConfig(dtype=dtype),
        compilation_config=CompilationConfig(
            custom_ops=["all"],
            pass_config=PassConfig(
                fuse_norm_quant=do_fusion,
                fuse_act_quant=do_fusion,
                eliminate_noops=True,
            ),
        ),
    )

    with set_current_vllm_config(vllm_config):
        assert RMSNorm.enabled()
        noop_pass = NoOpEliminationPass(vllm_config)
        fusion_pass = RMSNormQuantFusionPass(vllm_config)
        cleanup_pass = PostCleanupPass(vllm_config)
        act_quant_fusion_pass = ActivationQuantFusionPass(vllm_config)

        passes = (
            [noop_pass, fusion_pass, act_quant_fusion_pass, cleanup_pass]
            if do_fusion
            else [noop_pass, cleanup_pass]
        )
        func_pass = FixFunctionalizationPass(vllm_config)

        backend_func = TestBackend(*passes, func_pass)
        backend_no_func = TestBackend(*passes)

        model = model_class()
        inputs_func = model.example_inputs()
        inputs_no_func = copy.deepcopy(inputs_func)
        model_func = copy.deepcopy(model)
        model_no_func = copy.deepcopy(model)
        model_func = torch.compile(model_func, backend=backend_func)
        model_no_func = torch.compile(model_no_func, backend=backend_no_func)

        # deepcopy inputs to prevent potential in place mutation
        outputs_func = model_func(*copy.deepcopy(inputs_func))
        outputs_no_func = model_no_func(*copy.deepcopy(inputs_no_func))
        torch.testing.assert_close(outputs_func, outputs_no_func)

        # check if the functionalization pass is applied
        for op in model.ops_in_model(do_fusion):
            find_auto_fn(backend_no_func.graph_post_pass.nodes, op)
            assert find_auto_fn_maybe(backend_func.graph_post_pass.nodes, op) is None

        # make sure the ops were all de-functionalized
        found = dict()
        for node in backend_func.graph_post_pass.nodes:
            for op in model.ops_in_model(do_fusion):
                if is_func(node, op):
                    found[op] = True
            for op in model.ops_not_in_model():
                if is_func(node, op):
                    found[op] = True
        assert all(found[op] for op in model.ops_in_model(do_fusion))
        assert all(not found.get(op) for op in model.ops_not_in_model())