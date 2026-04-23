def _invoke(self, **kwargs):
        if self.check_if_canceled("Wikipedia processing"):
            return

        if not kwargs.get("query"):
            self.set_output("formalized_content", "")
            return ""

        last_e = ""
        for _ in range(self._param.max_retries+1):
            if self.check_if_canceled("Wikipedia processing"):
                return

            try:
                wikipedia.set_lang(self._param.language)
                wiki_engine = wikipedia
                pages = []
                for p in wiki_engine.search(kwargs["query"], results=self._param.top_n):
                    if self.check_if_canceled("Wikipedia processing"):
                        return

                    try:
                        pages.append(wikipedia.page(p))
                    except Exception:
                        pass
                self._retrieve_chunks(pages,
                                      get_title=lambda r: r.title,
                                      get_url=lambda r: r.url,
                                      get_content=lambda r: r.summary)
                return self.output("formalized_content")
            except Exception as e:
                if self.check_if_canceled("Wikipedia processing"):
                    return

                last_e = e
                logging.exception(f"Wikipedia error: {e}")
                time.sleep(self._param.delay_after_error)

        if last_e:
            self.set_output("_ERROR", str(last_e))
            return f"Wikipedia error: {last_e}"

        assert False, self.output()