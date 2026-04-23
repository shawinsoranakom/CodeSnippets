def call_function(
        self,
        tx: "InstructionTranslator",
        args: Sequence[VariableTracker],
        kwargs: "dict[str, VariableTracker]",
    ) -> "VariableTracker":
        from . import (
            DisabledSavedTensorsHooksVariable,
            DualLevelContextManager,
            FSDPParamGroupUseTrainingStateVariable,
            FxTracebackAnnotateVariable,
            GradIncrementNestingCtxManagerVariable,
            GradInplaceRequiresGradCtxManagerVariable,
            GradModeVariable,
            InferenceModeVariable,
            JvpIncrementNestingCtxManagerVariable,
            SDPAKernelVariable,
            SetFwdGradEnabledContextManager,
            StreamVariable,
            VmapIncrementNestingCtxManagerVariable,
        )

        if self.value is torch.no_grad:
            if len(args) == 1 and isinstance(
                args[0], variables.functions.BaseUserFunctionVariable
            ):
                ctx = GradModeVariable.create(tx, False)
                return ctx.call_function(tx, args, kwargs)
            else:
                return GradModeVariable.create(tx, False)
        elif self.value is torch.enable_grad:
            if len(args) == 1 and isinstance(
                args[0], variables.functions.BaseUserFunctionVariable
            ):
                ctx = GradModeVariable.create(tx, True)
                return ctx.call_function(tx, args, kwargs)
            return GradModeVariable.create(tx, True)
        elif self.value is torch.set_grad_enabled and len(args) == 1:
            return GradModeVariable.create(
                tx, args[0].as_python_constant(), initialized=True
            )
        elif self.value is torch.inference_mode:
            assert len(args) <= 1 and len(kwargs) == 0
            inf_mode = args[0].as_python_constant() if len(args) == 1 else True
            return InferenceModeVariable.create(tx, inf_mode)
        elif self.value in (
            torch.fx.traceback.annotate,
            torch.fx.traceback.annotate.__wrapped__,  # type: ignore[attr-defined]
        ):
            assert len(args) <= 1 and len(kwargs) == 0
            return FxTracebackAnnotateVariable(
                args[0].as_python_constant(), source=self.source
            )
        elif inspect.isclass(self.value) and issubclass(self.value, torch.Stream):
            from torch._dynamo.variables.builder import wrap_fx_proxy_cls

            return wrap_fx_proxy_cls(
                StreamVariable,
                tx,
                tx.output.create_proxy(
                    "call_function",
                    self.value,
                    (),
                    {},
                ),
            )
        elif self.value in (
            torch.amp.autocast_mode.autocast,
            torch.cuda.amp.autocast,
            torch.cpu.amp.autocast,
        ):
            # pyrefly: ignore [bad-argument-type]
            return AutocastModeVariable.create(self.value, args, kwargs)
        elif self.value in (
            torch.profiler.record_function,
            torch.autograd.profiler.record_function,
        ):
            return ProfilerRecordFunctionContextVariable.create(
                func=self.value, record_args=args, record_kwargs=kwargs
            )
        elif self.value in (
            torch.profiler.profile,
            torch.autograd.profiler.profile,
        ):
            warning_once(log, "Profiler function %s will be ignored", self.value)
            return ProfilerContextVariable()
        elif (
            self.value is torch._C.DisableTorchFunctionSubclass
            or self.value is torch._C.DisableTorchFunction
        ):
            assert not (args or kwargs)
            return TorchFunctionDisableVariable.create(
                tx, only_subclass=self.value is torch._C.DisableTorchFunctionSubclass
            )
        elif self.value is torch._functorch.vmap.vmap_increment_nesting:
            assert len(args) == 2
            return VmapIncrementNestingCtxManagerVariable.create(
                tx,
                args,
            )
        elif self.value is torch._functorch.eager_transforms.jvp_increment_nesting:
            assert len(args) == 0
            return JvpIncrementNestingCtxManagerVariable.create(tx)
        elif self.value is torch.autograd.forward_ad._set_fwd_grad_enabled:
            assert len(args) == 1
            return SetFwdGradEnabledContextManager.create(
                tx,
                [guard_if_dyn(x) for x in args],
            )
        elif self.value is torch.autograd.forward_ad.dual_level:
            assert len(args) == 0
            return DualLevelContextManager.create(tx)
        elif self.value is torch._functorch.eager_transforms.grad_increment_nesting:
            assert len(args) == 0
            return GradIncrementNestingCtxManagerVariable.create(tx)
        elif (
            self.value is torch._functorch.eager_transforms.enable_inplace_requires_grad
        ):
            assert len(args) == 1
            return GradInplaceRequiresGradCtxManagerVariable.create(
                tx,
                [guard_if_dyn(x) for x in args],
            )
        elif self.value is torch.autograd.graph.disable_saved_tensors_hooks:
            assert len(args) == 1
            return DisabledSavedTensorsHooksVariable.create(
                tx, args[0].as_python_constant()
            )
        elif (
            _fsdp_param_group is not None
            and self.value is _fsdp_param_group.FSDPParamGroup.use_training_state
        ):
            assert len(args) == 2
            return FSDPParamGroupUseTrainingStateVariable.create(
                tx, args[0], args[1].as_python_constant()
            )
        elif self.value is torch.nn.attention.sdpa_kernel.__wrapped__:  # type: ignore[attr-defined]
            name_to_arg_map = bind_args_cached(
                self.value,
                tx,
                self.source,
                args,
                kwargs,
            )
            backends = name_to_arg_map["backends"].as_python_constant()
            set_priority = name_to_arg_map["set_priority"].as_python_constant()
            return SDPAKernelVariable.create(tx, backends, set_priority)

        return super().call_function(tx, args, kwargs)