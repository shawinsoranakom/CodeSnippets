async def _invoke_async(self, **kwargs):
        if self.check_if_canceled("Retrieval processing"):
            return
        if not kwargs.get("query"):
            self.set_output("formalized_content", self._param.empty_response)
            return

        if hasattr(self._param, "retrieval_from") and self._param.retrieval_from == "dataset":
            return await self._retrieve_kb(kwargs["query"])
        elif hasattr(self._param, "retrieval_from") and self._param.retrieval_from == "memory":
            return await self._retrieve_memory(kwargs["query"])
        elif self._dataset_ids:
            return await self._retrieve_kb(kwargs["query"])
        elif hasattr(self._param, "memory_ids") and self._param.memory_ids:
            return await self._retrieve_memory(kwargs["query"])
        else:
            self.set_output("formalized_content", self._param.empty_response)
            return