async def _retrieve_information(self, search_query):
        """Retrieve information from different sources"""
        # 1. Knowledge base retrieval
        kbinfos = []
        try:
            kbinfos = await self._kb_retrieve(question=search_query) if self._kb_retrieve else {"chunks": [], "doc_aggs": []}
        except Exception as e:
            logging.error(f"Knowledge base retrieval error: {e}")

        # 2. Web retrieval (if Tavily API is configured)
        try:
            if self.internet_enabled and self.prompt_config.get("tavily_api_key"):
                tav = Tavily(self.prompt_config["tavily_api_key"])
                tav_res = tav.retrieve_chunks(search_query)
                kbinfos["chunks"].extend(tav_res["chunks"])
                kbinfos["doc_aggs"].extend(tav_res["doc_aggs"])
        except Exception as e:
            logging.error(f"Web retrieval error: {e}")

        # 3. Knowledge graph retrieval (if configured)
        try:
            if self.prompt_config.get("use_kg") and self._kg_retrieve:
                ck = await self._kg_retrieve(question=search_query)
                if ck["content_with_weight"]:
                    kbinfos["chunks"].insert(0, ck)
        except Exception as e:
            logging.error(f"Knowledge graph retrieval error: {e}")

        return kbinfos