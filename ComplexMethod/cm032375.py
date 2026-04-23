def _prepare_prompt_variables(self):
        self.imgs = []
        if self._param.visual_files_var:
            visual_val = self._canvas.get_variable_value(self._param.visual_files_var)
            self.imgs.extend(self._extract_data_images(visual_val))

        args = {}
        vars = self.get_input_elements() if not self._param.debug_inputs else self._param.debug_inputs
        extracted_imgs = []
        for k, o in vars.items():
            raw_value = o["value"]
            extracted_imgs.extend(self._extract_data_images(raw_value))
            args[k] = self._remove_data_images(raw_value)
            if args[k] is None:
                args[k] = ""
            if not isinstance(args[k], str):
                try:
                    args[k] = json.dumps(args[k], ensure_ascii=False)
                except Exception:
                    args[k] = str(args[k])
            self.set_input_value(k, args[k])

        self.imgs = self._uniq_images(self.imgs + extracted_imgs)
        if self.imgs and TenantLLMService.llm_id2llm_type(self._param.llm_id) == LLMType.CHAT.value:
            self.chat_mdl = LLMBundle(self._canvas.get_tenant_id(), LLMType.IMAGE2TEXT.value,
                                      self._param.llm_id, max_retries=self._param.max_retries,
                                      retry_interval=self._param.delay_after_error
                                      )

        msg, sys_prompt = self._sys_prompt_and_msg(self._canvas.get_history(self._param.message_history_window_size)[:-1], args)
        user_defined_prompt, sys_prompt = self._extract_prompts(sys_prompt)
        if self._param.cite and self._canvas.get_reference()["chunks"]:
            sys_prompt += citation_prompt(user_defined_prompt)

        return sys_prompt, msg, user_defined_prompt