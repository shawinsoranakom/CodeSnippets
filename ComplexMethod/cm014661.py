def test_circular_dependencies(self) -> None:
        """ Checks that all modules inside torch can be imported
        Prevents regression reported in https://github.com/pytorch/pytorch/issues/77441 """
        ignored_modules = ["torch.utils.tensorboard",  # deps on tensorboard
                           "torch.distributed.elastic.rendezvous",  # depps on etcd
                           "torch.backends._coreml",  # depends on pycoreml
                           "torch.contrib.",  # something weird
                           "torch.testing._internal.distributed.",  # just fails
                           "torch.ao.pruning._experimental.",  # depends on pytorch_lightning, not user-facing
                           "torch.onnx._internal",  # depends on onnx-script
                           "torch._inductor.runtime.triton_helpers",  # depends on triton
                           "torch._native.ops.bmm_outer_product.triton_kernels",  # depends on triton
                           "torch._inductor.codegen.cuda",  # depends on cutlass
                           "torch._inductor.codegen.cutedsl",  # depends on cutlass
                           "torch.distributed.benchmarks",  # depends on RPC and DDP Optim
                           "torch.distributed.debug._frontend",  # depends on tabulate
                           "torch.distributed.examples",  # requires CUDA and torchvision
                           "torch.distributed.tensor.examples",  # example scripts
                           "torch.distributed._tools.sac_ilp",  # depends on pulp
                           "torch.csrc",  # files here are devtools, not part of torch
                           "torch.include",  # torch include files after install
                           "torch._inductor.kernel.vendored_templates.cutedsl",  # depends on cutlass
                           ]
        if IS_WINDOWS or IS_MACOS or IS_JETSON:
            # Distributed should be importable on Windows(except nn.api.), but not on Mac
            if IS_MACOS or IS_JETSON:
                ignored_modules.append("torch.distributed.")
            else:
                ignored_modules.append("torch.distributed.nn.api.")
                ignored_modules.append("torch.distributed.optim.")
                ignored_modules.append("torch.distributed.rpc.")
            ignored_modules.append("torch.testing._internal.dist_utils")
            # And these both end up with transitive dependencies on distributed
            ignored_modules.append("torch.nn.parallel._replicated_tensor_ddp_interop")
            ignored_modules.append("torch.testing._internal.common_fsdp")
            ignored_modules.append("torch.testing._internal.common_distributed")

        if sys.version_info < (3, 12):
            # depends on Python 3.12+ syntax
            ignored_modules.append("torch.testing._internal.py312_intrinsics")

        torch_dir = os.path.dirname(torch.__file__)
        for base, _, files in os.walk(torch_dir):
            prefix = os.path.relpath(base, os.path.dirname(torch_dir)).replace(os.path.sep, ".")
            for f in files:
                if not f.endswith(".py"):
                    continue
                mod_name = f"{prefix}.{f[:-3]}" if f != "__init__.py" else prefix
                # Do not attempt to import executable modules
                if f == "__main__.py":
                    continue
                if any(mod_name.startswith(x) for x in ignored_modules):
                    continue
                try:
                    mod = importlib.import_module(mod_name)
                except Exception as e:
                    raise RuntimeError(f"Failed to import {mod_name}: {e}") from e
                self.assertTrue(inspect.ismodule(mod))