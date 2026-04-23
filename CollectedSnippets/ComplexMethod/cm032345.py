def _invoke(self, **kwargs):
        if self.check_if_canceled("DuckDuckGo processing"):
            return

        if not kwargs.get("query"):
            self.set_output("formalized_content", "")
            return ""

        last_e = ""
        for _ in range(self._param.max_retries+1):
            if self.check_if_canceled("DuckDuckGo processing"):
                return

            try:
                if kwargs.get("topic", "general") == "general":
                    with DDGS() as ddgs:
                        if self.check_if_canceled("DuckDuckGo processing"):
                            return

                        # {'title': '', 'href': '', 'body': ''}
                        duck_res = ddgs.text(kwargs["query"], max_results=self._param.top_n)

                        if self.check_if_canceled("DuckDuckGo processing"):
                            return

                        self._retrieve_chunks(duck_res,
                                              get_title=lambda r: r["title"],
                                              get_url=lambda r: r.get("href", r.get("url")),
                                              get_content=lambda r: r["body"])
                        self.set_output("json", duck_res)
                        return self.output("formalized_content")
                else:
                    with DDGS() as ddgs:
                        if self.check_if_canceled("DuckDuckGo processing"):
                            return

                        # {'date': '', 'title': '', 'body': '', 'url': '', 'image': '', 'source': ''}
                        duck_res = ddgs.news(kwargs["query"], max_results=self._param.top_n)

                        if self.check_if_canceled("DuckDuckGo processing"):
                            return

                        self._retrieve_chunks(duck_res,
                                              get_title=lambda r: r["title"],
                                              get_url=lambda r: r.get("href", r.get("url")),
                                              get_content=lambda r: r["body"])
                        self.set_output("json", duck_res)
                        return self.output("formalized_content")
            except Exception as e:
                if self.check_if_canceled("DuckDuckGo processing"):
                    return

                last_e = e
                logging.exception(f"DuckDuckGo error: {e}")
                time.sleep(self._param.delay_after_error)

        if last_e:
            self.set_output("_ERROR", str(last_e))
            return f"DuckDuckGo error: {last_e}"

        assert False, self.output()