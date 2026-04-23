async def _retrieve_memory(self, query_text: str):
        memory_ids: list[str] = [memory_id for memory_id in self._param.memory_ids]
        user_id: str = self._param.user_id if hasattr(self._param, "user_id") else None
        memory_list = MemoryService.get_by_ids(memory_ids)
        if not memory_list:
            raise Exception("No memory is selected.")

        embd_names = list({memory.embd_id for memory in memory_list})
        assert len(embd_names) == 1, "Memory use different embedding models."

        vars = self.get_input_elements_from_text(query_text)
        vars = {k: o["value"] for k, o in vars.items()}
        query = self.string_format(query_text, vars)
        # query message
        filter_dict: dict = {"memory_id": memory_ids}
        if user_id:
            import re
            # is variable
            if re.match(r"^{.*}$", user_id):
                user_id = self._canvas.get_variable_value(user_id)
            filter_dict["user_id"] = user_id
        message_list = memory_message_service.query_message(filter_dict, {
            "query": query,
            "similarity_threshold": self._param.similarity_threshold,
            "keywords_similarity_weight": self._param.keywords_similarity_weight,
            "top_n": self._param.top_n
        })
        if not message_list:
            self.set_output("formalized_content", self._param.empty_response)
            return ""
        formated_content = "\n".join(memory_prompt(message_list, 200000))
        # set formalized_content output
        self.set_output("formalized_content", formated_content)

        return formated_content