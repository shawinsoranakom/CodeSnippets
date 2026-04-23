def test_modules_can_be_imported(self):
        failures = []

        def onerror(modname):
            failures.append(
                (modname, ImportError("exception occurred importing package"))
            )

        for mod in pkgutil.walk_packages(torch.__path__, "torch.", onerror=onerror):
            modname = mod.name
            try:
                if "__main__" in modname:
                    continue
                importlib.import_module(modname)
            except Exception as e:
                # Some current failures are not ImportError
                log.exception("import_module failed")
                failures.append((modname, e))

        # It is ok to add new entries here but please be careful that these modules
        # do not get imported by public code.
        # DO NOT add public modules here.
        private_allowlist = {
            "torch._inductor.codegen.cutlass.cuda_kernel",
            # TODO(#133647): Remove the onnx._internal entries after
            # onnx and onnxscript are installed in CI.
            "torch.onnx._internal.exporter",
            "torch.onnx._internal.exporter._analysis",
            "torch.onnx._internal.exporter._building",
            "torch.onnx._internal.exporter._capture_strategies",
            "torch.onnx._internal.exporter._compat",
            "torch.onnx._internal.exporter._core",
            "torch.onnx._internal.exporter._decomp",
            "torch.onnx._internal.exporter._dispatching",
            "torch.onnx._internal.exporter._fx_passes",
            "torch.onnx._internal.exporter._ir_passes",
            "torch.onnx._internal.exporter._isolated",
            "torch.onnx._internal.exporter._onnx_program",
            "torch.onnx._internal.exporter._registration",
            "torch.onnx._internal.exporter._reporting",
            "torch.onnx._internal.exporter._schemas",
            "torch.onnx._internal.exporter._tensors",
            "torch.onnx._internal.exporter._torchlib.ops",
            "torch.onnx._internal.exporter._verification",
            "torch.onnx._internal.fx._pass",
            "torch.onnx._internal.fx.analysis",
            "torch.onnx._internal.fx.analysis.unsupported_nodes",
            "torch.onnx._internal.fx.decomposition_skip",
            "torch.onnx._internal.fx.diagnostics",
            "torch.onnx._internal.fx.fx_onnx_interpreter",
            "torch.onnx._internal.fx.fx_symbolic_graph_extractor",
            "torch.onnx._internal.fx.onnxfunction_dispatcher",
            "torch.onnx._internal.fx.op_validation",
            "torch.onnx._internal.fx.passes",
            "torch.onnx._internal.fx.passes._utils",
            "torch.onnx._internal.fx.passes.decomp",
            "torch.onnx._internal.fx.passes.functionalization",
            "torch.onnx._internal.fx.passes.modularization",
            "torch.onnx._internal.fx.passes.readability",
            "torch.onnx._internal.fx.passes.type_promotion",
            "torch.onnx._internal.fx.passes.virtualization",
            "torch.onnx._internal.fx.type_utils",
            "torch.testing._internal.common_distributed",
            "torch.testing._internal.common_fsdp",
            "torch.testing._internal.dist_utils",
            "torch.testing._internal.distributed.common_state_dict",
            "torch.testing._internal.distributed._shard.sharded_tensor",
            "torch.testing._internal.distributed._shard.test_common",
            "torch.testing._internal.distributed._tensor.common_dtensor",
            "torch.testing._internal.distributed.ddp_under_dist_autograd_test",
            "torch.testing._internal.distributed.distributed_test",
            "torch.testing._internal.distributed.distributed_utils",
            "torch.testing._internal.distributed.fake_pg",
            "torch.testing._internal.distributed.multi_threaded_pg",
            "torch.testing._internal.distributed.nn.api.remote_module_test",
            "torch.testing._internal.distributed.rpc.dist_autograd_test",
            "torch.testing._internal.distributed.rpc.dist_optimizer_test",
            "torch.testing._internal.distributed.rpc.examples.parameter_server_test",
            "torch.testing._internal.distributed.rpc.examples.reinforcement_learning_rpc_test",
            "torch.testing._internal.distributed.rpc.faulty_agent_rpc_test",
            "torch.testing._internal.distributed.rpc.faulty_rpc_agent_test_fixture",
            "torch.testing._internal.distributed.rpc.jit.dist_autograd_test",
            "torch.testing._internal.distributed.rpc.jit.rpc_test",
            "torch.testing._internal.distributed.rpc.jit.rpc_test_faulty",
            "torch.testing._internal.distributed.rpc.rpc_agent_test_fixture",
            "torch.testing._internal.distributed.rpc.rpc_test",
            "torch.testing._internal.distributed.rpc.tensorpipe_rpc_agent_test_fixture",
            "torch.testing._internal.distributed.rpc_utils",
            "torch.testing._internal.py312_intrinsics",
            "torch._inductor.codegen.cutlass.cuda_template",
            "torch._inductor.codegen.cutedsl._cutedsl_utils",
            "torch._inductor.codegen.cuda.gemm_template",
            "torch._inductor.codegen.cpp_template",
            "torch._inductor.codegen.cpp_gemm_template",
            "torch._inductor.codegen.cpp_micro_gemm",
            "torch._inductor.codegen.cpp_template_kernel",
            "torch._inductor.kernel.vendored_templates.cutedsl.kernels.cutedsl_grouped_gemm",  # depends on cutlass
            "torch._inductor.kernel.vendored_templates.cutedsl.dense_blockscaled_gemm_persistent",  # depends on cutlass
            "torch._inductor.kernel.vendored_templates.cutedsl.wrappers",  # depends on cutlass_api
            "torch._inductor.kernel.vendored_templates.cutedsl.wrappers.dense_blockscaled_gemm_kernel",  # depends on cutlass_api
            "torch._inductor.runtime.triton_helpers",
            "torch.ao.pruning._experimental.data_sparsifier.lightning.callbacks.data_sparsity",
            "torch.backends._coreml.preprocess",
            "torch.contrib._tensorboard_vis",
            "torch.distributed._composable",
            "torch.distributed._functional_collectives",
            "torch.distributed._functional_collectives_impl",
            "torch.distributed._shard",
            "torch.distributed._sharded_tensor",
            "torch.distributed._sharding_spec",
            "torch.distributed._spmd.api",
            "torch.distributed._spmd.batch_dim_utils",
            "torch.distributed._spmd.comm_tensor",
            "torch.distributed._spmd.data_parallel",
            "torch.distributed._spmd.distribute",
            "torch.distributed._spmd.experimental_ops",
            "torch.distributed._spmd.parallel_mode",
            "torch.distributed._tensor",
            "torch.distributed._tools.sac_ilp",
            "torch.distributed.algorithms._checkpoint.checkpoint_wrapper",
            "torch.distributed.algorithms._optimizer_overlap",
            "torch.distributed.rpc._testing.faulty_agent_backend_registry",
            "torch.distributed.rpc._utils",
            "torch.ao.pruning._experimental.data_sparsifier.benchmarks.dlrm_utils",
            "torch.ao.pruning._experimental.data_sparsifier.benchmarks.evaluate_disk_savings",
            "torch.ao.pruning._experimental.data_sparsifier.benchmarks.evaluate_forward_time",
            "torch.ao.pruning._experimental.data_sparsifier.benchmarks.evaluate_model_metrics",
            "torch.ao.pruning._experimental.data_sparsifier.lightning.tests.test_callbacks",
            "torch.csrc.jit.tensorexpr.scripts.bisect",
            "torch.csrc.lazy.test_mnist",
            "torch.distributed._shard.checkpoint._fsspec_filesystem",
            "torch.distributed._tensor.examples.visualize_sharding_example",
            "torch.distributed.checkpoint._fsspec_filesystem",
            "torch.distributed.examples.memory_tracker_example",
            "torch.testing._internal.distributed.rpc.fb.thrift_rpc_agent_test_fixture",
            "torch.utils._cxx_pytree",
            "torch.utils.tensorboard._convert_np",
            "torch.utils.tensorboard._embedding",
            "torch.utils.tensorboard._onnx_graph",
            "torch.utils.tensorboard._proto_graph",
            "torch.utils.tensorboard._pytorch_graph",
            "torch.utils.tensorboard._utils",
        }

        errors = []
        for mod, exc in failures:
            if mod in private_allowlist or (
                mod.startswith("torch._native.ops.") and "triton" in mod
            ):
                if self._is_mod_public(mod):
                    raise AssertionError(
                        f"Expected private module name to include '_' segments: {mod}"
                    )
                continue
            errors.append(
                f"{mod} failed to import with error {type(exc).__qualname__}: {str(exc)}"
            )
        self.assertEqual("", "\n".join(errors))