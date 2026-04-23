async def execute_async(self, prompt, prompt_id, extra_data={}, execute_outputs=[]):
        set_preview_method(extra_data.get("preview_method"))

        nodes.interrupt_processing(False)

        if "client_id" in extra_data:
            self.server.client_id = extra_data["client_id"]
        else:
            self.server.client_id = None

        self.status_messages = []
        self.add_message("execution_start", { "prompt_id": prompt_id}, broadcast=False)

        self._notify_prompt_lifecycle("start", prompt_id)
        ram_headroom = int(self.cache_args["ram"] * (1024 ** 3))
        ram_release_callback = self.caches.outputs.ram_release if self.cache_type == CacheType.RAM_PRESSURE else None
        comfy.memory_management.set_ram_cache_release_state(ram_release_callback, ram_headroom)

        try:
            with torch.inference_mode():
                dynamic_prompt = DynamicPrompt(prompt)
                reset_progress_state(prompt_id, dynamic_prompt)
                add_progress_handler(WebUIProgressHandler(self.server))
                is_changed_cache = IsChangedCache(prompt_id, dynamic_prompt, self.caches.outputs)
                for cache in self.caches.all:
                    await cache.set_prompt(dynamic_prompt, prompt.keys(), is_changed_cache)
                    cache.clean_unused()

                node_ids = list(prompt.keys())
                cache_results = await asyncio.gather(
                    *(self.caches.outputs.get(node_id) for node_id in node_ids)
                )
                cached_nodes = [
                    node_id for node_id, result in zip(node_ids, cache_results)
                    if result is not None
                ]

                comfy.model_management.cleanup_models_gc()
                self.add_message("execution_cached",
                              { "nodes": cached_nodes, "prompt_id": prompt_id},
                              broadcast=False)
                pending_subgraph_results = {}
                pending_async_nodes = {} # TODO - Unify this with pending_subgraph_results
                ui_node_outputs = {}
                executed = set()
                execution_list = ExecutionList(dynamic_prompt, self.caches.outputs)
                current_outputs = self.caches.outputs.all_node_ids()
                for node_id in list(execute_outputs):
                    execution_list.add_node(node_id)

                while not execution_list.is_empty():
                    node_id, error, ex = await execution_list.stage_node_execution()
                    if error is not None:
                        self.handle_execution_error(prompt_id, dynamic_prompt.original_prompt, current_outputs, executed, error, ex)
                        break

                    assert node_id is not None, "Node ID should not be None at this point"
                    result, error, ex = await execute(self.server, dynamic_prompt, self.caches, node_id, extra_data, executed, prompt_id, execution_list, pending_subgraph_results, pending_async_nodes, ui_node_outputs)
                    self.success = result != ExecutionResult.FAILURE
                    if result == ExecutionResult.FAILURE:
                        self.handle_execution_error(prompt_id, dynamic_prompt.original_prompt, current_outputs, executed, error, ex)
                        break
                    elif result == ExecutionResult.PENDING:
                        execution_list.unstage_node_execution()
                    else: # result == ExecutionResult.SUCCESS:
                        execution_list.complete_node_execution()

                    if self.cache_type == CacheType.RAM_PRESSURE:
                        comfy.model_management.free_memory(0, None, pins_required=ram_headroom, ram_required=ram_headroom)
                        comfy.memory_management.extra_ram_release(ram_headroom)
                else:
                    # Only execute when the while-loop ends without break
                    # Send cached UI for intermediate output nodes that weren't executed
                    for node_id in dynamic_prompt.all_node_ids():
                        if node_id in executed:
                            continue
                        if not _is_intermediate_output(dynamic_prompt, node_id):
                            continue
                        cached = await self.caches.outputs.get(node_id)
                        if cached is not None:
                            display_node_id = dynamic_prompt.get_display_node_id(node_id)
                            _send_cached_ui(self.server, node_id, display_node_id, cached, prompt_id, ui_node_outputs)
                    self.add_message("execution_success", { "prompt_id": prompt_id }, broadcast=False)

                ui_outputs = {}
                meta_outputs = {}
                for node_id, ui_info in ui_node_outputs.items():
                    ui_outputs[node_id] = ui_info["output"]
                    meta_outputs[node_id] = ui_info["meta"]
                self.history_result = {
                    "outputs": ui_outputs,
                    "meta": meta_outputs,
                }
                self.server.last_node_id = None
                if comfy.model_management.DISABLE_SMART_MEMORY:
                    comfy.model_management.unload_all_models()
        finally:
            comfy.memory_management.set_ram_cache_release_state(None, 0)
            self._notify_prompt_lifecycle("end", prompt_id)