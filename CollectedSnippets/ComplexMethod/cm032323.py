async def run(self, **kwargs):
        self.globals["sys.date"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        st = time.perf_counter()
        self._loop = asyncio.get_running_loop()
        self.message_id = get_uuid()
        created_at = int(time.time())
        self.add_user_input(kwargs.get("query"))
        for k, cpn in self.components.items():
            self.components[k]["obj"].reset(True)

        if kwargs.get("webhook_payload"):
            for k, cpn in self.components.items():
                if self.components[k]["obj"].component_name.lower() == "begin"  and self.components[k]["obj"]._param.mode == "Webhook":
                    payload = kwargs.get("webhook_payload", {})
                    if "input" in payload:
                        self.components[k]["obj"].set_input_value("request", payload["input"])
                    for kk, vv in payload.items():
                        if kk == "input":
                            continue
                        self.components[k]["obj"].set_output(kk, vv)

        layout_recognize = None
        for cpn in self.components.values():
            if cpn["obj"].component_name.lower() == "begin":
                layout_recognize = getattr(cpn["obj"]._param, "layout_recognize", None)
                break

        for k in kwargs.keys():
            if k in ["query", "user_id", "files"] and kwargs[k]:
                if k == "files":
                    self.globals[f"sys.{k}"] = await self.get_files_async(kwargs[k], layout_recognize)
                else:
                    self.globals[f"sys.{k}"] = kwargs[k]
        if not self.globals["sys.conversation_turns"] :
            self.globals["sys.conversation_turns"] = 0
        self.globals["sys.conversation_turns"] += 1

        def decorate(event, dt):
            nonlocal created_at
            return {
                "event": event,
                #"conversation_id": "f3cc152b-24b0-4258-a1a1-7d5e9fc8a115",
                "message_id": self.message_id,
                "created_at": created_at,
                "task_id": self.task_id,
                "data": dt
            }

        if not self.path or self.path[-1].lower().find("userfillup") < 0:
            self.path.append("begin")
            self.retrieval.append({"chunks": [], "doc_aggs": []})

        if self.is_canceled():
            msg = f"Task {self.task_id} has been canceled before starting."
            logging.info(msg)
            raise TaskCanceledException(msg)

        yield decorate("workflow_started", {"inputs": kwargs.get("inputs")})
        self.retrieval.append({"chunks": {}, "doc_aggs": {}})

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

        def _node_finished(cpn_obj):
            return decorate("node_finished",{
                           "inputs": cpn_obj.get_input_values(),
                           "outputs": cpn_obj.output(),
                           "component_id": cpn_obj._id,
                           "component_name": self.get_component_name(cpn_obj._id),
                           "component_type": self.get_component_type(cpn_obj._id),
                           "error": cpn_obj.error(),
                           "elapsed_time": time.perf_counter() - cpn_obj.output("_created_time"),
                           "created_at": cpn_obj.output("_created_time"),
                       })

        self.error = ""
        idx = len(self.path) - 1
        partials = []
        tts_mdl = None
        while idx < len(self.path):
            to = len(self.path)
            for i in range(idx, to):
                yield decorate("node_started", {
                    "inputs": None, "created_at": int(time.time()),
                    "component_id": self.path[i],
                    "component_name": self.get_component_name(self.path[i]),
                    "component_type": self.get_component_type(self.path[i]),
                    "thoughts": self.get_component_thoughts(self.path[i])
                })
            await _run_batch(idx, to)
            to = len(self.path)
            # post-processing of components invocation
            for i in range(idx, to):
                cpn = self.get_component(self.path[i])
                cpn_obj = self.get_component_obj(self.path[i])
                if cpn_obj.component_name.lower() == "message":
                    if cpn_obj.get_param("auto_play"):
                        tts_model_config = get_tenant_default_model_by_type(self._tenant_id, LLMType.TTS)
                        tts_mdl = LLMBundle(self._tenant_id, tts_model_config)
                    if isinstance(cpn_obj.output("content"), partial):
                        _m = ""
                        buff_m = ""
                        stream = cpn_obj.output("content")()
                        async def _process_stream(m):
                            nonlocal buff_m, _m, tts_mdl
                            if not m:
                                return
                            if m == "<think>":
                                return decorate("message", {"content": "", "start_to_think": True})

                            elif m == "</think>":
                                return decorate("message", {"content": "", "end_to_think": True})

                            buff_m += m
                            _m += m

                            if len(buff_m) > 16:
                                ev = decorate(
                                    "message",
                                    {
                                        "content": m,
                                        "audio_binary": self.tts(tts_mdl, buff_m)
                                    }
                                )
                                buff_m = ""
                                return ev

                            return decorate("message", {"content": m})

                        if inspect.isasyncgen(stream):
                            async for m in stream:
                                ev= await _process_stream(m)
                                if ev:
                                    yield ev
                        else:
                            for m in stream:
                                ev= await _process_stream(m)
                                if ev:
                                    yield ev
                        if buff_m:
                            yield decorate("message", {"content": "", "audio_binary": self.tts(tts_mdl, buff_m)})
                            buff_m = ""
                        cpn_obj.set_output("content", _m)
                    else:
                        yield decorate("message", {"content": cpn_obj.output("content")})

                    message_end = self._build_message_end(cpn_obj)
                    yield decorate("message_end", message_end)

                    while partials:
                        _cpn_obj = self.get_component_obj(partials[0])
                        if isinstance(_cpn_obj.output("content"), partial):
                            break
                        yield _node_finished(_cpn_obj)
                        partials.pop(0)

                other_branch = False
                if cpn_obj.error():
                    ex = cpn_obj.exception_handler()
                    if ex and ex["goto"]:
                        self.path.extend(ex["goto"])
                        other_branch = True
                    elif ex and ex["default_value"]:
                        yield decorate("message", {"content": ex["default_value"]})
                        yield decorate("message_end", {})
                    else:
                        self.error = cpn_obj.error()

                if cpn_obj.component_name.lower() not in ("iteration","loop"):
                    if isinstance(cpn_obj.output("content"), partial):
                        if self.error:
                            cpn_obj.set_output("content", None)
                            yield _node_finished(cpn_obj)
                        else:
                            partials.append(self.path[i])
                    else:
                        yield _node_finished(cpn_obj)

                def _append_path(cpn_id):
                    nonlocal other_branch
                    if other_branch:
                        return
                    if self.path[-1] == cpn_id:
                        return
                    self.path.append(cpn_id)

                def _extend_path(cpn_ids):
                    nonlocal other_branch
                    if other_branch:
                        return
                    for cpn_id in cpn_ids:
                        _append_path(cpn_id)

                if cpn_obj.component_name.lower() in ("iterationitem","loopitem") and cpn_obj.end():
                    iter = cpn_obj.get_parent()
                    yield _node_finished(iter)
                    _extend_path(self.get_component(cpn["parent_id"])["downstream"])
                elif cpn_obj.component_name.lower() in ["categorize", "switch"]:
                    _extend_path(cpn_obj.output("_next"))
                elif cpn_obj.component_name.lower() in ("iteration", "loop"):
                    _append_path(cpn_obj.get_start())
                elif cpn_obj.component_name.lower() == "exitloop" and cpn_obj.get_parent().component_name.lower() == "loop":
                    _extend_path(self.get_component(cpn["parent_id"])["downstream"])
                elif not cpn["downstream"] and cpn_obj.get_parent():
                    _append_path(cpn_obj.get_parent().get_start())
                else:
                    _extend_path(cpn["downstream"])

            if self.error:
                logging.error(f"Runtime Error: {self.error}")
                break
            idx = to

            if any([self.get_component_obj(c).component_name.lower() == "userfillup" for c in self.path[idx:]]):
                path = [c for c in self.path[idx:] if self.get_component(c)["obj"].component_name.lower() == "userfillup"]
                path.extend([c for c in self.path[idx:] if self.get_component(c)["obj"].component_name.lower() != "userfillup"])
                another_inputs = {}
                tips = ""
                for c in path:
                    o = self.get_component_obj(c)
                    if o.component_name.lower() == "userfillup":
                        o.invoke()
                        another_inputs.update(o.get_input_elements())
                        if o.get_param("enable_tips"):
                            tips = o.output("tips")
                self.path = path
                yield decorate("user_inputs", {"inputs": another_inputs, "tips": tips})
                return
        self.path = self.path[:idx]
        if not self.error:
            yield decorate("workflow_finished",
                       {
                           "inputs": kwargs.get("inputs"),
                           "outputs": self.get_component_obj(self.path[-1]).output(),
                           "elapsed_time": time.perf_counter() - st,
                           "created_at": st,
                       })
            self.history.append(("assistant", self.get_component_obj(self.path[-1]).output()))
            self.globals["sys.history"].append(f"{self.history[-1][0]}: {self.history[-1][1]}")
        elif "Task has been canceled" in self.error:
            yield decorate("workflow_finished",
                       {
                           "inputs": kwargs.get("inputs"),
                           "outputs": "Task has been canceled",
                           "elapsed_time": time.perf_counter() - st,
                           "created_at": st,
                       })