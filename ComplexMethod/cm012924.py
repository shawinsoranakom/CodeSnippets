def _extract_logger_info_one_model(
    model: nn.Module,
    results: NSResultsType,
    logger_cls: Callable,
) -> None:
    torch._C._log_api_usage_once(
        "quantization_api._numeric_suite_fx._extract_logger_info_one_model"
    )
    for _gm_name, mod in model.named_modules():
        # TODO(future PR): better check when scripted
        is_logger = isinstance(mod, logger_cls) or (  # type: ignore[arg-type]
            isinstance(mod, torch.jit.RecursiveScriptModule)
            and mod.original_name == "OutputLogger"
        )
        if is_logger:
            key = mod.ref_name
            if key not in results:
                results[key] = {}
            if mod.model_name in results[key]:
                raise AssertionError(f"{mod.model_name} is already present in results")
            if mod.results_type not in results[key]:
                results[key][mod.results_type] = {}
            if mod.model_name not in results[key][mod.results_type]:
                results[key][mod.results_type][mod.model_name] = []
            stats_to_use = mod.stats
            if len(mod.stats_rnn) > 0:
                stats_to_use = mod.stats_rnn
            data = {
                "type": mod.results_type,
                "values": stats_to_use,
                "ref_node_name": mod.ref_node_name,
                "ref_node_target_type": mod.ref_node_target_type,
                "prev_node_name": mod.prev_node_name,
                "prev_node_target_type": mod.prev_node_target_type,
                "index_within_arg": mod.index_within_arg,
                "index_of_arg": mod.index_of_arg,
                "fqn": mod.fqn,
                "qconfig_str": mod.qconfig_str,
            }
            if hasattr(mod, "comparisons"):
                data["comparisons"] = mod.comparisons
                data["comparison_fn_name"] = mod.comparison_fn_name
            else:
                data["comparisons"] = []
                data["comparison_fn_name"] = ""
            results[key][mod.results_type][mod.model_name].append(data)
            # ensure the list stays sorted
            results[key][mod.results_type][mod.model_name].sort(
                key=lambda res: f"{res['index_of_arg']}:{res['index_within_arg']}"
            )