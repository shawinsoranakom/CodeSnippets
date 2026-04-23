def _check_can_cache(gm: torch.fx.GraphModule) -> None:
        """
        Check some conditions that would preclude caching and raise BypassFxGraphCache
        to bypass in case caching is not possible.
        """
        # Custom passes must implement the CustomGraphPass or we don't
        # know how to include them in the cache key calculation.
        # When timing is EARLY, pre-grad passes already ran before the cache
        # lookup so there's nothing to validate here.
        if resolve_pre_grad_pass_timing() != "early":
            assert not config.pre_grad_custom_pass or (
                isinstance(config.pre_grad_custom_pass, CustomGraphPass)
                and config.pre_grad_custom_pass.uuid()
            ), "Unsupported pre grad custom pass"
        for p in (config.post_grad_custom_pre_pass, config.post_grad_custom_post_pass):
            if p and (not isinstance(p, CustomGraphPass) or not p.uuid()):
                raise BypassFxGraphCache("Unsupported post grad custom pass")
        # Same with the joint custom passes
        for p in (config.joint_custom_pre_pass, config.joint_custom_post_pass):
            if p and (not isinstance(p, CustomGraphPass) or not p.uuid()):
                raise BypassFxGraphCache("Unsupported joint custom pass")
        # We should find any users of _pre_fusion_custom_pass and _fuse_ddp_communication_passes
        # and ensure they are not passing us raw callables
        if config._pre_fusion_custom_pass is not None:
            if not isinstance(config._pre_fusion_custom_pass, CustomGraphPass):
                raise BypassFxGraphCache("Unsupported _pre_fusion_custom_pass")
        for p in config._fuse_ddp_communication_passes:
            if callable(p) and not isinstance(p, CustomGraphPass):
                raise BypassFxGraphCache("Unsupported _fuse_ddp_communication_pass")

        # Freezing can embed constants that wouldn't be static across runs.
        if has_frozen_params(gm) and not torch._utils_internal.justknobs_check(
            "pytorch/inductor:allow_freezing_with_caching"
        ):
            raise BypassFxGraphCache("Skipping graph with frozen constants")

        if config.aot_inductor.use_runtime_constant_folding:
            raise BypassFxGraphCache(
                "Runtime constant folding can introduce constants that aren't "
                "static across runs"
            )

        from torch._inductor.compiler_bisector import CompilerBisector

        if CompilerBisector.bisection_enabled:
            log.debug("dont cache graph when bisect enabled")
            raise BypassFxGraphCache

        # The treatment of guards in the caching implementation requires that
        # we have a shape env.
        if FxGraphCache._get_shape_env() is None:
            log.debug("fx graph cache no shape env")
            raise BypassFxGraphCache("No shape env")

        # We skip caching if there are any HOPs or torchbind objects.
        FxGraphCache._check_for_hop(gm)