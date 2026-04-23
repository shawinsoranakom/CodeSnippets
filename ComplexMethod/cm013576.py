def _compile_submod(gm: torch.fx.GraphModule, prefix: str) -> torch.fx.GraphModule:
    from torch._inductor.standalone_compile import AOTCompiledArtifact

    for node in gm.graph.nodes:
        if node.op == "call_module" and node.target.startswith(prefix):
            fake_inputs = []
            for inp_node in node.all_input_nodes:
                if hasattr(inp_node, "meta") and "val" in inp_node.meta:
                    fake_inputs.append(inp_node.meta["val"])
                else:
                    raise RuntimeError(
                        f"Partition is bad because non fake tensor value is seen {inp_node}"
                    )

            submod = getattr(gm, node.target)

            # Get inductor configs from annotation
            # TODO we should change partition when there are multiple differently
            # annotated regions.
            inductor_options: dict[str, Any] = {}
            for sub_node in submod.graph.nodes:
                if hasattr(sub_node, "meta") and sub_node.meta.get("custom", None):
                    custom = sub_node.meta["custom"]
                    if isinstance(custom, dict) and "compile_with_inductor" in custom:
                        compile_value = custom["compile_with_inductor"]
                        if (
                            isinstance(compile_value, dict)
                            and "inductor_configs" in compile_value
                        ):
                            inductor_options = compile_value["inductor_configs"]
                            break

            # Log the options being used
            logger.info(
                "Compiling submodule %s with inductor options: %s",
                node.target,
                inductor_options,
            )

            # Apply config patches before compilation
            import torch._inductor.config as inductor_config

            # Validate that all config keys exist
            for key in inductor_options:
                if not hasattr(inductor_config, key):
                    raise ValueError(
                        f"Invalid inductor config key '{key}' in regional_inductor annotation. "
                        f"Available config keys can be found in torch._inductor.config"
                    )

            with (
                inductor_config.patch(inductor_options),
                _disable_remat_for_regional_subcompile(),
            ):
                compiled_fn = torch._inductor.standalone_compile(
                    submod,
                    fake_inputs,
                    dynamic_shapes="from_tracing_context",
                    aot=True,
                )
            if not isinstance(compiled_fn, AOTCompiledArtifact):
                raise AssertionError(
                    f"Expected AOTCompiledArtifact, got {type(compiled_fn)}"
                )
            # _dummy_wrapper is to make call_function happy
            compiled_submod = _dummy_wrapper(compiled_fn)
            with gm.graph.inserting_after(node):
                new_node = gm.graph.call_function(
                    compiled_submod, args=node.args, kwargs=node.kwargs
                )
                new_node.meta = node.meta
                node.replace_all_uses_with(new_node)
                gm.graph.erase_node(node)
                del gm._modules[node.target]

    gm.recompile()
    return gm