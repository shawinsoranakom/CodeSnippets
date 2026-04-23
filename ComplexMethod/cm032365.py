def _invoke(self, **kwargs):
        if self.check_if_canceled("ArXiv processing"):
            return

        if not kwargs.get("query"):
            self.set_output("formalized_content", "")
            return ""

        last_e = ""
        for _ in range(self._param.max_retries+1):
            if self.check_if_canceled("ArXiv processing"):
                return

            try:
                sort_choices = {"relevance": arxiv.SortCriterion.Relevance,
                                "lastUpdatedDate": arxiv.SortCriterion.LastUpdatedDate,
                                'submittedDate': arxiv.SortCriterion.SubmittedDate}
                arxiv_client = arxiv.Client()
                search = arxiv.Search(
                    query=kwargs["query"],
                    max_results=self._param.top_n,
                    sort_by=sort_choices[self._param.sort_by]
                )
                results = list(arxiv_client.results(search))

                if self.check_if_canceled("ArXiv processing"):
                    return

                self._retrieve_chunks(results,
                                      get_title=lambda r: r.title,
                                      get_url=lambda r: r.pdf_url,
                                      get_content=lambda r: r.summary)
                return self.output("formalized_content")
            except Exception as e:
                if self.check_if_canceled("ArXiv processing"):
                    return

                last_e = e
                logging.exception(f"ArXiv error: {e}")
                time.sleep(self._param.delay_after_error)

        if last_e:
            self.set_output("_ERROR", str(last_e))
            return f"ArXiv error: {last_e}"

        assert False, self.output()