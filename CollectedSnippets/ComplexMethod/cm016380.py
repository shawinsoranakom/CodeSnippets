async def process_inputs(inputs, index=None, input_is_list=False):
        if allow_interrupt:
            nodes.before_node_execution()
        execution_block = None
        for k, v in inputs.items():
            if input_is_list:
                for e in v:
                    if isinstance(e, ExecutionBlocker):
                        v = e
                        break
            if isinstance(v, ExecutionBlocker):
                execution_block = execution_block_cb(v) if execution_block_cb else v
                break
        if execution_block is None:
            if pre_execute_cb is not None and index is not None:
                pre_execute_cb(index)
            # V3
            if isinstance(obj, _ComfyNodeInternal) or (is_class(obj) and issubclass(obj, _ComfyNodeInternal)):
                # if is just a class, then assign no state, just create clone
                if is_class(obj):
                    type_obj = obj
                    obj.VALIDATE_CLASS()
                    class_clone = obj.PREPARE_CLASS_CLONE(v3_data)
                # otherwise, use class instance to populate/reuse some fields
                else:
                    type_obj = type(obj)
                    type_obj.VALIDATE_CLASS()
                    class_clone = type_obj.PREPARE_CLASS_CLONE(v3_data)
                f = make_locked_method_func(type_obj, func, class_clone)
                # in case of dynamic inputs, restructure inputs to expected nested dict
                if v3_data is not None:
                    inputs = _io.build_nested_inputs(inputs, v3_data)
            # V1
            else:
                f = getattr(obj, func)
            if inspect.iscoroutinefunction(f):
                async def async_wrapper(f, prompt_id, unique_id, list_index, args):
                    with CurrentNodeContext(prompt_id, unique_id, list_index):
                        return await f(**args)
                task = asyncio.create_task(async_wrapper(f, prompt_id, unique_id, index, args=inputs))
                # Give the task a chance to execute without yielding
                await asyncio.sleep(0)
                if task.done():
                    result = task.result()
                    results.append(result)
                else:
                    results.append(task)
            else:
                with CurrentNodeContext(prompt_id, unique_id, index):
                    result = f(**inputs)
                results.append(result)
        else:
            results.append(execution_block)