def _invoke(self, **kwargs):
        if self.check_if_canceled("PubMed processing"):
            return

        if not kwargs.get("query"):
            self.set_output("formalized_content", "")
            return ""

        last_e = ""
        for _ in range(self._param.max_retries+1):
            if self.check_if_canceled("PubMed processing"):
                return

            try:
                Entrez.email = self._param.email
                pubmedids = Entrez.read(Entrez.esearch(db='pubmed', retmax=self._param.top_n, term=kwargs["query"]))['IdList']

                if self.check_if_canceled("PubMed processing"):
                    return

                pubmedcnt = ET.fromstring(re.sub(r'<(/?)b>|<(/?)i>', '', Entrez.efetch(db='pubmed', id=",".join(pubmedids),
                                                                                       retmode="xml").read().decode("utf-8")))

                if self.check_if_canceled("PubMed processing"):
                    return

                self._retrieve_chunks(pubmedcnt.findall("PubmedArticle"),
                                      get_title=lambda child: child.find("MedlineCitation").find("Article").find("ArticleTitle").text,
                                      get_url=lambda child: "https://pubmed.ncbi.nlm.nih.gov/" + child.find("MedlineCitation").find("PMID").text,
                                      get_content=lambda child: self._format_pubmed_content(child),)
                return self.output("formalized_content")
            except Exception as e:
                if self.check_if_canceled("PubMed processing"):
                    return

                last_e = e
                logging.exception(f"PubMed error: {e}")
                time.sleep(self._param.delay_after_error)

        if last_e:
            self.set_output("_ERROR", str(last_e))
            return f"PubMed error: {last_e}"

        assert False, self.output()