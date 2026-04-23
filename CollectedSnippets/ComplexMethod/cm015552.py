def check_gradients(
    config: PipelineTestConfig,
    stage_modules,
    ref_mod,
    submod_names=None,
    rtol=1e-5,
    atol=4e-5,
):
    """Check that gradients match between pipeline stages and reference model using flexible comparison."""

    def grad_check(grad1, grad2, param_name, rtol, atol, tolerance=0.05):
        if grad1 is None and grad2 is None:
            return
        if grad1 is None or grad2 is None:
            raise AssertionError(
                f"One gradient is None for {param_name}: {grad1} vs {grad2}"
            )
        try:
            torch.testing.assert_close(grad1, grad2, rtol=rtol, atol=atol)
        except AssertionError:
            print(
                f"Numerical issues detected for {param_name}: param grad {grad1} vs ref grad {grad2}"
            )
            raise

    if submod_names is None:
        # Single stage case - need to detect tracer vs manual pipeline
        stage_modules = [stage_modules]

        # Try to detect if this is a tracer-based pipeline by checking if parameter exists in ref_mod
        sample_param_name = next(iter(stage_modules[0].named_parameters()))[0]
        try:
            # Try to get parameter directly from reference model (tracer-based)
            ref_mod.get_parameter(sample_param_name)
            is_tracer_based = True
        except AttributeError:
            # Parameter doesn't exist at root level, must be manual pipeline
            is_tracer_based = False

        if is_tracer_based:
            # Tracer-based pipeline: parameter names are full paths from root model
            for name, p in stage_modules[0].named_parameters():
                ref_p = ref_mod.get_parameter(name)
                grad_check(p.grad, ref_p.grad, name, rtol, atol)
        else:
            # Manual pipeline: parameter names are local to the submodule
            submod_name = f"layers.{config.rank}"
            ref_submod = ref_mod.get_submodule(submod_name)
            for name, p in stage_modules[0].named_parameters():
                ref_p = ref_submod.get_parameter(name)
                grad_check(p.grad, ref_p.grad, f"{submod_name}.{name}", rtol, atol)
    else:
        # Multi-stage case - always use submodule approach
        for stage_module, submod_name in zip(stage_modules, submod_names):
            ref_submod = ref_mod.get_submodule(submod_name)
            for name, p in stage_module.named_parameters():
                ref_p = ref_submod.get_parameter(name)
                grad_check(p.grad, ref_p.grad, f"{submod_name}.{name}", rtol, atol)