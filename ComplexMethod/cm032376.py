async def _invoke_async(self, **kwargs):
        if self.check_if_canceled("LLM processing"):
            return

        def clean_formated_answer(ans: str) -> str:
            ans = re.sub(r"^.*</think>", "", ans, flags=re.DOTALL)
            ans = re.sub(r"^.*```json", "", ans, flags=re.DOTALL)
            return re.sub(r"```\n*$", "", ans, flags=re.DOTALL)

        prompt, msg, _ = self._prepare_prompt_variables()
        error: str = ""
        output_structure = None
        try:
            output_structure = self._param.outputs["structured"]
        except Exception:
            pass
        if output_structure and isinstance(output_structure, dict) and output_structure.get("properties") and len(output_structure["properties"]) > 0:
            schema = json.dumps(output_structure, ensure_ascii=False, indent=2)
            prompt_with_schema = prompt + structured_output_prompt(schema)
            for _ in range(self._param.max_retries + 1):
                if self.check_if_canceled("LLM processing"):
                    return

                _, msg_fit = message_fit_in(
                    [{"role": "system", "content": prompt_with_schema}, *deepcopy(msg)],
                    int(self.chat_mdl.max_length * 0.97),
                )
                error = ""
                ans = await self._generate_async(msg_fit)
                msg_fit.pop(0)
                if ans.find("**ERROR**") >= 0:
                    logging.error(f"LLM response error: {ans}")
                    error = ans
                    continue
                try:
                    self.set_output("structured", json_repair.loads(clean_formated_answer(ans)))
                    return
                except Exception:
                    msg_fit.append({"role": "user", "content": "The answer can't not be parsed as JSON"})
                    error = "The answer can't not be parsed as JSON"
            if error:
                self.set_output("_ERROR", error)
            return

        downstreams = self._canvas.get_component(self._id)["downstream"] if self._canvas.get_component(self._id) else []
        ex = self.exception_handler()
        if any([self._canvas.get_component_obj(cid).component_name.lower() == "message" for cid in downstreams]) and not (
            ex and ex["goto"]
        ):
            self.set_output("content", partial(self._stream_output_async, prompt, deepcopy(msg)))
            return

        error = ""
        for _ in range(self._param.max_retries + 1):
            if self.check_if_canceled("LLM processing"):
                return

            _, msg_fit = message_fit_in(
                [{"role": "system", "content": prompt}, *deepcopy(msg)], int(self.chat_mdl.max_length * 0.97)
            )
            error = ""
            ans = await self._generate_async(msg_fit)
            msg_fit.pop(0)
            if ans.find("**ERROR**") >= 0:
                logging.error(f"LLM response error: {ans}")
                error = ans
                continue
            self.set_output("content", ans)
            break

        if error:
            if self.get_exception_default_value():
                self.set_output("content", self.get_exception_default_value())
            else:
                self.set_output("_ERROR", error)