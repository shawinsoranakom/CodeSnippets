def make_entry(
        compiled_fw_func: OutputCode,
        compiled_bw_func: OutputCode | None,
        aot_joint_graph_str: str | None,
        aot_forward_graph_str: str | None,
        aot_backward_graph_str: str | None,
        runtime_metadata: ViewAndMutationMeta,
        dispatch_wrappers: list[CompilerWrapper],
        maybe_subclass_meta: SubclassMeta | None,
        num_fw_outs_saved_for_bw: int | None,
        indices_of_inps_to_detach: list[int],
        forward_time_taken_ns: int,
        backward_time_taken_ns: int,
        sanitized_aot_config: AOTConfig,
        guards_expr: str | None,
        backward_state_indices: list[int] | None,
        num_symints_saved_for_bw: int | None,
        serialized_bw_module: SerializedGraphModule | None,
    ) -> GenericAOTAutogradResult[Any, Any]:
        if should_bundle_autograd_cache():
            # Helper function to unwrap all the wrappers we added during aotdispatch
            # They get reapplied on cache load
            def unwrap_output_code(obj: object) -> OutputCode:
                while hasattr(obj, "__wrapped__"):
                    obj = obj.__wrapped__
                if not isinstance(obj, OutputCode):
                    raise AssertionError(f"expected OutputCode, got {type(obj)}")
                return obj

            compiled_fw_graph = unwrap_output_code(compiled_fw_func)
            bundled_compiled_forward = BundledCompiledForward(compiled_fw_graph)
            bundled_compiled_backward = None
            if compiled_bw_func is not None:
                if backward_state_indices is None:
                    raise AssertionError("backward_state_indices must not be None")
                if num_symints_saved_for_bw is None:
                    raise AssertionError("num_symints_saved_for_bw must not be None")
                compiled_bw_graph = unwrap_output_code(compiled_bw_func)
                bundled_compiled_backward = BundledCompiledBackward(
                    compiled_bw_graph, backward_state_indices, num_symints_saved_for_bw
                )

            return BundledAOTAutogradResult(
                compiled_fw=bundled_compiled_forward,
                compiled_bw=bundled_compiled_backward,
                aot_joint_graph_str=aot_joint_graph_str,
                aot_forward_graph_str=aot_forward_graph_str,
                aot_backward_graph_str=aot_backward_graph_str,
                runtime_metadata=runtime_metadata,
                dispatch_wrappers=dispatch_wrappers,
                maybe_subclass_meta=maybe_subclass_meta,
                num_fw_outs_saved_for_bw=num_fw_outs_saved_for_bw,
                indices_of_inps_to_detach=indices_of_inps_to_detach,
                forward_time_taken_ns=forward_time_taken_ns,
                backward_time_taken_ns=backward_time_taken_ns,
                sanitized_aot_config=sanitized_aot_config,
                guards_expr=guards_expr,
                serialized_bw_module=serialized_bw_module,
            )

        else:
            fw_key = getattr(compiled_fw_func, "_fx_graph_cache_key", None)
            fw_debug_lines = getattr(
                compiled_fw_func, "_fx_graph_cache_debug_lines", []
            )

            if fw_key is None:
                raise AssertionError("fw_key must not be None")
            compiled_forward = CompiledForward(
                fx_graph_cache_info=(fw_key, fw_debug_lines),
                fx_graph_guard_expr=getattr(compiled_fw_func, "guards_expr", None),
            )
            compiled_backward = None
            if compiled_bw_func is not None:
                bw_key = getattr(compiled_bw_func, "_fx_graph_cache_key", None)
                bw_debug_lines = getattr(
                    compiled_bw_func, "_fx_graph_cache_debug_lines", []
                )
                if bw_key is None:
                    raise AssertionError("bw_key must not be None")
                if backward_state_indices is None:
                    raise AssertionError("backward_state_indices must not be None")
                if num_symints_saved_for_bw is None:
                    raise AssertionError("num_symints_saved_for_bw must not be None")
                compiled_backward = CompiledBackward(
                    fx_graph_cache_info=(bw_key, bw_debug_lines),
                    fx_graph_guard_expr=getattr(compiled_bw_func, "guards_expr", None),
                    backward_state_indices=backward_state_indices,
                    num_symints_saved_for_bw_=num_symints_saved_for_bw,
                )

            return AOTAutogradResult(
                compiled_fw=compiled_forward,
                compiled_bw=compiled_backward,
                aot_joint_graph_str=aot_joint_graph_str,
                aot_forward_graph_str=aot_forward_graph_str,
                aot_backward_graph_str=aot_backward_graph_str,
                runtime_metadata=runtime_metadata,
                dispatch_wrappers=dispatch_wrappers,
                maybe_subclass_meta=maybe_subclass_meta,
                num_fw_outs_saved_for_bw=num_fw_outs_saved_for_bw,
                indices_of_inps_to_detach=indices_of_inps_to_detach,
                forward_time_taken_ns=forward_time_taken_ns,
                backward_time_taken_ns=backward_time_taken_ns,
                sanitized_aot_config=sanitized_aot_config,
                guards_expr=guards_expr,
                serialized_bw_module=serialized_bw_module,
            )