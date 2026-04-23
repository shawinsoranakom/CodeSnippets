def _invoke(self, **kwargs):
        if self.check_if_canceled("GoogleScholar processing"):
            return

        if not kwargs.get("query"):
            self.set_output("formalized_content", "")
            return ""

        last_e = ""
        for _ in range(self._param.max_retries+1):
            if self.check_if_canceled("GoogleScholar processing"):
                return

            try:
                scholar_client = scholarly.search_pubs(kwargs["query"], patents=self._param.patents, year_low=self._param.year_low,
                                                       year_high=self._param.year_high, sort_by=self._param.sort_by)

                if self.check_if_canceled("GoogleScholar processing"):
                    return

                self._retrieve_chunks(scholar_client,
                                      get_title=lambda r: r['bib']['title'],
                                      get_url=lambda r: r["pub_url"],
                                      get_content=lambda r: "\n author: " + ",".join(r['bib']['author']) + '\n Abstract: ' + r['bib'].get('abstract', 'no abstract')
                                      )
                self.set_output("json", list(scholar_client))
                return self.output("formalized_content")
            except Exception as e:
                if self.check_if_canceled("GoogleScholar processing"):
                    return

                last_e = e
                logging.exception(f"GoogleScholar error: {e}")
                time.sleep(self._param.delay_after_error)

        if last_e:
            self.set_output("_ERROR", str(last_e))
            return f"GoogleScholar error: {last_e}"

        assert False, self.output()