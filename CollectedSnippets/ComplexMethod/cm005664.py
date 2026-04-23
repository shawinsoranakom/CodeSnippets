def recursively_install_hooks(
    parent_module: nn.Module, module_name: str, capture_tasks: list[tuple[str, OutputRecorder]]
) -> None:
    """
    Recursively install all output capturing hooks on all submodules of `parent_module`.
    Note that we need to use this recursive approach instead of simply iterating over all modules, because we want
    to respect the `capture_tasks` of all individual submodels (`PreTrainedModel` instances) in the graph. That is, once
    we reach a submodel in the graph, its children should use this submodel's `capture_tasks`, but other parts of the graph
    should not.
    """
    from ..modeling_utils import PreTrainedModel

    # First dispatch to children if needed
    for name, module in parent_module.named_children():
        # Keep dispatching the same `capture_tasks`
        if not isinstance(module, PreTrainedModel):
            recursively_install_hooks(module, f"{module_name}.{name}", capture_tasks)
        # New Submodel: we need to dispatch its own `capture_tasks`
        else:
            install_all_output_capturing_hooks(module, prefix=f"{module_name}.{name}")

    # Potentially install the hook on current `parent_module`
    for key, specs in capture_tasks:
        # The second check is for multimodals where only backbone layer suffix is available
        if (specs.target_class is not None and isinstance(parent_module, specs.target_class)) or (
            specs.class_name is not None and module_name.endswith(specs.class_name)
        ):
            if specs.layer_name is not None and specs.layer_name not in module_name:
                continue
            install_output_capturing_hook(parent_module, key, specs.index)