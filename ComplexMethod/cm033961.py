def results_thread_main(strategy: StrategyBase) -> None:
    value: object

    while True:
        try:
            result = strategy._final_q.get()
            if isinstance(result, StrategySentinel):
                break
            elif isinstance(result, DisplaySend):
                dmethod = getattr(display, result.method)
                dmethod(*result.args, **result.kwargs)
            elif isinstance(result, CallbackSend):
                task_result = strategy._convert_wire_task_result_to_host_task_result(result.wire_task_result)
                strategy._tqm.send_callback(result.method_name, task_result)
            elif isinstance(result, WireTaskResult):
                result = strategy._convert_wire_task_result_to_host_task_result(result)
                with strategy._results_lock:
                    strategy._results.append(result)
            elif isinstance(result, PromptSend):
                try:
                    value = display.prompt_until(
                        result.prompt,
                        private=result.private,
                        seconds=result.seconds,
                        complete_input=result.complete_input,
                        interrupt_input=result.interrupt_input,
                    )
                except AnsibleError as e:
                    value = e
                except BaseException as e:
                    # relay unexpected errors so bugs in display are reported and don't cause workers to hang
                    try:
                        raise AnsibleError(f"{e}") from e
                    except AnsibleError as e:
                        value = e
                strategy._workers[result.worker_id].worker_queue.put(value)
            else:
                display.warning('Received an invalid object (%s) in the result queue: %r' % (type(result), result))
        except (OSError, EOFError):
            break
        except queue.Empty:
            pass