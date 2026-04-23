async def _invoke_async(self, **kwargs):
        if self.check_if_canceled("Agent processing"):
            return

        if kwargs.get("user_prompt"):
            usr_pmt = ""
            if kwargs.get("reasoning"):
                usr_pmt += "\nREASONING:\n{}\n".format(kwargs["reasoning"])
            if kwargs.get("context"):
                usr_pmt += "\nCONTEXT:\n{}\n".format(kwargs["context"])
            if usr_pmt:
                usr_pmt += "\nQUERY:\n{}\n".format(str(kwargs["user_prompt"]))
            else:
                usr_pmt = str(kwargs["user_prompt"])
            self._param.prompts = [{"role": "user", "content": usr_pmt}]

        if not self.tools:
            if self.check_if_canceled("Agent processing"):
                return
            return await LLM._invoke_async(self, **kwargs)

        prompt, msg, user_defined_prompt = self._prepare_prompt_variables()
        output_schema = self._get_output_schema()
        schema_prompt = ""
        if output_schema:
            schema = json.dumps(output_schema, ensure_ascii=False, indent=2)
            schema_prompt = structured_output_prompt(schema)

        component = self._canvas.get_component(self._id)
        downstreams = component["downstream"] if component else []
        ex = self.exception_handler()
        has_message_downstream = any(self._canvas.get_component_obj(cid).component_name.lower() == "message" for cid in downstreams)
        if has_message_downstream and not (ex and ex["goto"]) and not output_schema:
            self.set_output("content", partial(self.stream_output_with_tools_async, prompt, deepcopy(msg), user_defined_prompt))
            return

        msg = self._fit_messages(prompt, msg)
        self._append_system_prompt(msg, schema_prompt)
        ans = await self._generate_async(msg)

        if ans.find("**ERROR**") >= 0:
            logging.error(f"Agent._chat got error. response: {ans}")
            if self.get_exception_default_value():
                self.set_output("content", self.get_exception_default_value())
            else:
                self.set_output("_ERROR", ans)
            return

        if output_schema:
            error = ""
            for _ in range(self._param.max_retries + 1):
                try:
                    obj = json_repair.loads(self._clean_formatted_answer(ans))
                    self.set_output("structured", obj)
                    return obj
                except Exception:
                    error = "The answer cannot be parsed as JSON"
                    ans = await self._force_format_to_schema_async(ans, schema_prompt)
                    if ans.find("**ERROR**") >= 0:
                        continue

            self.set_output("_ERROR", error)
            return

        artifact_md = self._collect_tool_artifact_markdown(existing_text=ans)
        if artifact_md:
            ans += "\n\n" + artifact_md
        self.set_output("content", ans)
        return ans