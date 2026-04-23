def load(cls, model, example_inputs, mode):
        import torch._inductor
        from torch.export.dynamic_shapes import _combine_args, _tree_map_with_path

        key = weakref.ref(model)
        if key not in cls.cache:
            # Register the output dataclass to pytree
            example_args, example_kwargs = _normalize_bench_inputs(example_inputs)
            with torch.no_grad():
                # copy.deepcopy is required to prevent any surprising side-effect,
                # see https://github.com/pytorch/pytorch/issues/113029
                # This will cause memory stats to be overshadowed by this eager run.
                # To fix that, memory stats will be reset later.
                example_outputs = copy.deepcopy(model)(*example_args, **example_kwargs)

            if pytree.is_namedtuple_instance(example_outputs):
                typ = type(example_outputs)
                pytree._register_namedtuple(
                    typ,
                    serialized_type_name=f"{typ.__module__}.{typ.__name__}",
                )
            else:
                _register_dataclass_output_as_pytree(example_outputs)

            combined_args = _combine_args(model, example_args, example_kwargs)
            dynamic_shapes = _tree_map_with_path(
                _produce_dynamic_shapes_for_export, combined_args
            )

            # delete example_outputs and reset memory stats here
            del example_outputs
            if current_device == "cuda":
                empty_gpu_cache(current_device)
                torch.cuda.reset_peak_memory_stats()
                pre_clone_memory_used = torch.cuda.max_memory_allocated()
            elif current_device == "hpu":
                torch.hpu.reset_peak_memory_stats()
                pre_clone_memory_used = torch.hpu.max_memory_allocated()

            # Clone the model pre-exporting.  This prevents scenarios observed in a few
            # models, where the forward pass modifies model state while exporting, and
            # FakeTensors are thus saved as model data members.  This invalidates model
            # reuse in eager mode, so it's safest to export a model clone.
            model_clone = copy.deepcopy(model)

            # Since CPU doesn't monitor max memory allocation, anything measuring peak
            # memory will miss our transient model clone on CPU anyway.
            #
            # The justification for tracking this value (in order to remove it from the
            # AOTInductor memory measurements) is that normal usage of AOTInductor would
            # not clone the model, since the eager model would be unused post-export.
            clone_memory_used = 0.0
            if current_device == "cuda":
                clone_memory_used = (
                    torch.cuda.max_memory_allocated() - pre_clone_memory_used
                ) / 1e9
            elif current_device == "hpu":
                clone_memory_used = (
                    torch.hpu.max_memory_allocated() - pre_clone_memory_used
                ) / 1e9

            inductor_configs = {}
            if mode == "max-autotune":
                inductor_configs["max_autotune"] = True
            ep = torch.export.export(
                model_clone,
                example_args,
                example_kwargs,
                dynamic_shapes=dynamic_shapes,
                strict=False,
            )
            with torch.no_grad():
                package_path = torch._inductor.aoti_compile_and_package(
                    ep, inductor_configs=inductor_configs
                )  # type: ignore[arg-type]

            cls.cache[key] = (
                torch._inductor.aoti_load_package(package_path),
                clone_memory_used,
            )

        return cls.cache[key][0]