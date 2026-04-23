async def execute(server, dynprompt, caches, current_item, extra_data, executed, prompt_id, execution_list, pending_subgraph_results, pending_async_nodes, ui_outputs):
    unique_id = current_item
    real_node_id = dynprompt.get_real_node_id(unique_id)
    display_node_id = dynprompt.get_display_node_id(unique_id)
    parent_node_id = dynprompt.get_parent_node_id(unique_id)
    inputs = dynprompt.get_node(unique_id)['inputs']
    class_type = dynprompt.get_node(unique_id)['class_type']
    class_def = nodes.NODE_CLASS_MAPPINGS[class_type]
    cached = await caches.outputs.get(unique_id)
    if cached is not None:
        _send_cached_ui(server, unique_id, display_node_id, cached, prompt_id, ui_outputs)
        get_progress_state().finish_progress(unique_id)
        execution_list.cache_update(unique_id, cached)
        return (ExecutionResult.SUCCESS, None, None)

    input_data_all = None
    try:
        if unique_id in pending_async_nodes:
            results = []
            for r in pending_async_nodes[unique_id]:
                if isinstance(r, asyncio.Task):
                    try:
                        results.append(r.result())
                    except Exception as ex:
                        # An async task failed - propagate the exception up
                        del pending_async_nodes[unique_id]
                        raise ex
                else:
                    results.append(r)
            del pending_async_nodes[unique_id]
            output_data, output_ui, has_subgraph = get_output_from_returns(results, class_def)
        elif unique_id in pending_subgraph_results:
            cached_results = pending_subgraph_results[unique_id]
            resolved_outputs = []
            for is_subgraph, result in cached_results:
                if not is_subgraph:
                    resolved_outputs.append(result)
                else:
                    resolved_output = []
                    for r in result:
                        if is_link(r):
                            source_node, source_output = r[0], r[1]
                            node_cached = execution_list.get_cache(source_node, unique_id)
                            for o in node_cached.outputs[source_output]:
                                resolved_output.append(o)

                        else:
                            resolved_output.append(r)
                    resolved_outputs.append(tuple(resolved_output))
            output_data = merge_result_data(resolved_outputs, class_def)
            output_ui = []
            del pending_subgraph_results[unique_id]
            has_subgraph = False
        else:
            get_progress_state().start_progress(unique_id)
            input_data_all, missing_keys, v3_data = get_input_data(inputs, class_def, unique_id, execution_list, dynprompt, extra_data)
            if server.client_id is not None:
                server.last_node_id = display_node_id
                server.send_sync("executing", { "node": unique_id, "display_node": display_node_id, "prompt_id": prompt_id }, server.client_id)

            obj = await caches.objects.get(unique_id)
            if obj is None:
                obj = class_def()
                await caches.objects.set(unique_id, obj)

            if issubclass(class_def, _ComfyNodeInternal):
                lazy_status_present = first_real_override(class_def, "check_lazy_status") is not None
            else:
                lazy_status_present = getattr(obj, "check_lazy_status", None) is not None
            if lazy_status_present:
                # for check_lazy_status, the returned data should include the original key of the input
                v3_data_lazy = v3_data.copy()
                v3_data_lazy["create_dynamic_tuple"] = True
                required_inputs = await _async_map_node_over_list(prompt_id, unique_id, obj, input_data_all, "check_lazy_status", allow_interrupt=True, v3_data=v3_data_lazy)
                required_inputs = await resolve_map_node_over_list_results(required_inputs)
                required_inputs = set(sum([r for r in required_inputs if isinstance(r,list)], []))
                required_inputs = [x for x in required_inputs if isinstance(x,str) and (
                    x not in input_data_all or x in missing_keys
                )]
                if len(required_inputs) > 0:
                    for i in required_inputs:
                        execution_list.make_input_strong_link(unique_id, i)
                    return (ExecutionResult.PENDING, None, None)

            def execution_block_cb(block):
                if block.message is not None:
                    mes = {
                        "prompt_id": prompt_id,
                        "node_id": unique_id,
                        "node_type": class_type,
                        "executed": list(executed),

                        "exception_message": f"Execution Blocked: {block.message}",
                        "exception_type": "ExecutionBlocked",
                        "traceback": [],
                        "current_inputs": [],
                        "current_outputs": [],
                    }
                    server.send_sync("execution_error", mes, server.client_id)
                    return ExecutionBlocker(None)
                else:
                    return block
            def pre_execute_cb(call_index):
                # TODO - How to handle this with async functions without contextvars (which requires Python 3.12)?
                GraphBuilder.set_default_prefix(unique_id, call_index, 0)

            try:
                output_data, output_ui, has_subgraph, has_pending_tasks = await get_output_data(prompt_id, unique_id, obj, input_data_all, execution_block_cb=execution_block_cb, pre_execute_cb=pre_execute_cb, v3_data=v3_data)
            finally:
                if comfy.memory_management.aimdo_enabled:
                    if args.verbose == "DEBUG":
                        comfy_aimdo.control.analyze()
                    comfy.model_management.reset_cast_buffers()
                    comfy_aimdo.model_vbar.vbars_reset_watermark_limits()

            if has_pending_tasks:
                pending_async_nodes[unique_id] = output_data
                unblock = execution_list.add_external_block(unique_id)
                async def await_completion():
                    tasks = [x for x in output_data if isinstance(x, asyncio.Task)]
                    await asyncio.gather(*tasks, return_exceptions=True)
                    unblock()
                asyncio.create_task(await_completion())
                return (ExecutionResult.PENDING, None, None)
        if len(output_ui) > 0:
            ui_outputs[unique_id] = {
                "meta": {
                    "node_id": unique_id,
                    "display_node": display_node_id,
                    "parent_node": parent_node_id,
                    "real_node_id": real_node_id,
                },
                "output": output_ui
            }
            if server.client_id is not None:
                server.send_sync("executed", { "node": unique_id, "display_node": display_node_id, "output": output_ui, "prompt_id": prompt_id }, server.client_id)
        if has_subgraph:
            cached_outputs = []
            new_node_ids = []
            new_output_ids = []
            new_output_links = []
            for i in range(len(output_data)):
                new_graph, node_outputs = output_data[i]
                if new_graph is None:
                    cached_outputs.append((False, node_outputs))
                else:
                    for node_id, node_info in new_graph.items():
                        new_node_ids.append(node_id)
                        display_id = node_info.get("override_display_id", unique_id)
                        dynprompt.add_ephemeral_node(node_id, node_info, unique_id, display_id)
                        # Figure out if the newly created node is an output node
                        class_type = node_info["class_type"]
                        class_def = nodes.NODE_CLASS_MAPPINGS[class_type]
                        if hasattr(class_def, 'OUTPUT_NODE') and class_def.OUTPUT_NODE == True:
                            new_output_ids.append(node_id)
                    for i in range(len(node_outputs)):
                        if is_link(node_outputs[i]):
                            from_node_id, from_socket = node_outputs[i][0], node_outputs[i][1]
                            new_output_links.append((from_node_id, from_socket))
                    cached_outputs.append((True, node_outputs))
            new_node_ids = set(new_node_ids)
            for cache in caches.all:
                subcache = await cache.ensure_subcache_for(unique_id, new_node_ids)
                subcache.clean_unused()
            for node_id in new_output_ids:
                execution_list.add_node(node_id)
                execution_list.cache_link(node_id, unique_id)
            for link in new_output_links:
                execution_list.add_strong_link(link[0], link[1], unique_id)
            pending_subgraph_results[unique_id] = cached_outputs
            return (ExecutionResult.PENDING, None, None)

        cache_entry = CacheEntry(ui=ui_outputs.get(unique_id), outputs=output_data)
        execution_list.cache_update(unique_id, cache_entry)
        await caches.outputs.set(unique_id, cache_entry)

    except comfy.model_management.InterruptProcessingException as iex:
        logging.info("Processing interrupted")

        # skip formatting inputs/outputs
        error_details = {
            "node_id": real_node_id,
        }

        return (ExecutionResult.FAILURE, error_details, iex)
    except Exception as ex:
        typ, _, tb = sys.exc_info()
        exception_type = full_type_name(typ)
        input_data_formatted = {}
        if input_data_all is not None:
            input_data_formatted = {}
            for name, inputs in input_data_all.items():
                input_data_formatted[name] = [format_value(x) for x in inputs]

        logging.error(f"!!! Exception during processing !!! {ex}")
        logging.error(traceback.format_exc())
        tips = ""

        if comfy.model_management.is_oom(ex):
            tips = "This error means you ran out of memory on your GPU.\n\nTIPS: If the workflow worked before you might have accidentally set the batch_size to a large number."
            logging.info("Memory summary: {}".format(comfy.model_management.debug_memory_summary()))
            logging.error("Got an OOM, unloading all loaded models.")
            comfy.model_management.unload_all_models()
        elif isinstance(ex, RuntimeError) and ("mat1 and mat2 shapes" in str(ex)) and "Sampler" in class_type:
            tips = "\n\nTIPS: If you have any \"Load CLIP\" or \"*CLIP Loader\" nodes in your workflow connected to this sampler node make sure the correct file(s) and type is selected."

        error_details = {
            "node_id": real_node_id,
            "exception_message": "{}\n{}".format(ex, tips),
            "exception_type": exception_type,
            "traceback": traceback.format_tb(tb),
            "current_inputs": input_data_formatted
        }

        return (ExecutionResult.FAILURE, error_details, ex)

    get_progress_state().finish_progress(unique_id)
    executed.add(unique_id)

    return (ExecutionResult.SUCCESS, None, None)