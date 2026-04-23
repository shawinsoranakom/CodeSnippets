def _invoke(self, **kwargs):
        if self.check_if_canceled("TavilyExtract processing"):
            return

        self.tavily_client = TavilyClient(api_key=self._param.api_key)
        last_e = None
        for fld in ["urls", "extract_depth", "format"]:
            if fld not in kwargs:
                kwargs[fld] = getattr(self._param, fld)
        if kwargs.get("urls") and isinstance(kwargs["urls"], str):
            kwargs["urls"] = kwargs["urls"].split(",")
        for _ in range(self._param.max_retries+1):
            if self.check_if_canceled("TavilyExtract processing"):
                return

            try:
                kwargs["include_images"] = False
                res = self.tavily_client.extract(**kwargs)
                if self.check_if_canceled("TavilyExtract processing"):
                    return

                self.set_output("json", res["results"])
                return self.output("json")
            except Exception as e:
                if self.check_if_canceled("TavilyExtract processing"):
                    return

                last_e = e
                logging.exception(f"Tavily error: {e}")
        if last_e:
            self.set_output("_ERROR", str(last_e))
            return f"Tavily error: {last_e}"

        assert False, self.output()