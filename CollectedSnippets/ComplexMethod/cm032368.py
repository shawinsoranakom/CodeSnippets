def _invoke(self, **kwargs):
        if self.check_if_canceled("TavilySearch processing"):
            return

        if not kwargs.get("query"):
            self.set_output("formalized_content", "")
            return ""

        self.tavily_client = TavilyClient(api_key=self._param.api_key)
        last_e = None
        for fld in ["search_depth", "topic", "max_results", "days", "include_answer", "include_raw_content", "include_images", "include_image_descriptions", "include_domains", "exclude_domains"]:
            if fld not in kwargs:
                kwargs[fld] = getattr(self._param, fld)
        for _ in range(self._param.max_retries+1):
            if self.check_if_canceled("TavilySearch processing"):
                return

            try:
                kwargs["include_images"] = False
                kwargs["include_raw_content"] = False
                res = self.tavily_client.search(**kwargs)
                if self.check_if_canceled("TavilySearch processing"):
                    return

                self._retrieve_chunks(res["results"],
                                      get_title=lambda r: r["title"],
                                      get_url=lambda r: r["url"],
                                      get_content=lambda r: r["raw_content"] if r["raw_content"] else r["content"],
                                      get_score=lambda r: r["score"])
                self.set_output("json", res["results"])
                return self.output("formalized_content")
            except Exception as e:
                if self.check_if_canceled("TavilySearch processing"):
                    return

                last_e = e
                logging.exception(f"Tavily error: {e}")
                time.sleep(self._param.delay_after_error)
        if last_e:
            self.set_output("_ERROR", str(last_e))
            return f"Tavily error: {last_e}"

        assert False, self.output()