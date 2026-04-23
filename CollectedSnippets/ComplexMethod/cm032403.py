async def _invoke_async(self, **kwargs):
        if self.check_if_canceled("Categorize processing"):
            return

        msg = self._canvas.get_history(self._param.message_history_window_size)
        if not msg:
            msg = [{"role": "user", "content": ""}]
        query_key = self._param.query or "sys.query"
        if query_key in kwargs:
            query_value = kwargs[query_key]
        else:
            query_value = self._canvas.get_variable_value(query_key)
        if query_value is None:
            query_value = ""
        msg[-1]["content"] = query_value
        self.set_input_value(query_key, msg[-1]["content"])
        self._param.update_prompt()
        chat_model_config = get_model_config_by_type_and_name(self._canvas.get_tenant_id(), LLMType.CHAT, self._param.llm_id)
        chat_mdl = LLMBundle(self._canvas.get_tenant_id(), chat_model_config)

        user_prompt = """
---- Real Data ----
{} →
""".format(" | ".join(["{}: \"{}\"".format(c["role"].upper(), re.sub(r"\n", "", c["content"], flags=re.DOTALL)) for c in msg]))

        if self.check_if_canceled("Categorize processing"):
            return

        ans = await chat_mdl.async_chat(self._param.sys_prompt, [{"role": "user", "content": user_prompt}], self._param.gen_conf())
        logging.info(f"input: {user_prompt}, answer: {str(ans)}")
        if ERROR_PREFIX in ans:
            raise Exception(ans)

        if self.check_if_canceled("Categorize processing"):
            return

        # Count the number of times each category appears in the answer.
        category_counts = {}
        for c in self._param.category_description.keys():
            count = ans.lower().count(c.lower())
            category_counts[c] = count

        cpn_ids = list(self._param.category_description.items())[-1][1]["to"]
        max_category = list(self._param.category_description.keys())[-1]
        if any(category_counts.values()):
            max_category = max(category_counts.items(), key=lambda x: x[1])[0]
            cpn_ids = self._param.category_description[max_category]["to"]

        self.set_output("category_name", max_category)
        self.set_output("_next", cpn_ids)