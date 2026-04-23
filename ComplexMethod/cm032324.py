async def _run_batch(f, t):
            if self.is_canceled():
                msg = f"Task {self.task_id} has been canceled during batch execution."
                logging.info(msg)
                raise TaskCanceledException(msg)

            loop = asyncio.get_running_loop()
            tasks = []
            max_concurrency = getattr(self._thread_pool, "_max_workers", 5)
            sem = asyncio.Semaphore(max_concurrency)

            async def _invoke_one(cpn_obj, sync_fn, call_kwargs, use_async: bool):
                async with sem:
                    if use_async:
                        await cpn_obj.invoke_async(**(call_kwargs or {}))
                        return
                    await loop.run_in_executor(self._thread_pool, partial(sync_fn, **(call_kwargs or {})))

            i = f
            while i < t:
                cpn = self.get_component_obj(self.path[i])
                task_fn = None
                call_kwargs = None

                if cpn.component_name.lower() in ["begin", "userfillup"]:
                    call_kwargs = {"inputs": kwargs.get("inputs", {})}
                    task_fn = cpn.invoke
                    i += 1
                else:
                    for _, ele in cpn.get_input_elements().items():
                        if isinstance(ele, dict) and ele.get("_cpn_id") and ele.get("_cpn_id") not in self.path[:i] and self.path[0].lower().find("userfillup") < 0:
                            self.path.pop(i)
                            t -= 1
                            break
                    else:
                        call_kwargs = cpn.get_input()
                        task_fn = cpn.invoke
                        i += 1

                if task_fn is None:
                    continue

                fn_invoke_async = getattr(cpn, "_invoke_async", None)
                use_async = (fn_invoke_async and asyncio.iscoroutinefunction(fn_invoke_async)) or asyncio.iscoroutinefunction(getattr(cpn, "_invoke", None))
                tasks.append(asyncio.create_task(_invoke_one(cpn, task_fn, call_kwargs, use_async)))

            if tasks:
                await asyncio.gather(*tasks)