def _invoke(self, **kwargs):
        if self.check_if_canceled("Google processing"):
            return

        if not kwargs.get("q"):
            self.set_output("formalized_content", "")
            return ""

        params = {
            "api_key": self._param.api_key,
            "engine": "google",
            "q": kwargs["q"],
            "google_domain": "google.com",
            "gl": self._param.country,
            "hl": self._param.language
        }
        last_e = ""
        for _ in range(self._param.max_retries+1):
            if self.check_if_canceled("Google processing"):
                return

            try:
                search = GoogleSearch(params).get_dict()

                if self.check_if_canceled("Google processing"):
                    return

                self._retrieve_chunks(search["organic_results"],
                                      get_title=lambda r: r["title"],
                                      get_url=lambda r: r["link"],
                                      get_content=lambda r: r.get("about_this_result", {}).get("source", {}).get("description", r["snippet"])
                                      )
                self.set_output("json", search["organic_results"])
                return self.output("formalized_content")
            except Exception as e:
                if self.check_if_canceled("Google processing"):
                    return

                last_e = e
                logging.exception(f"Google error: {e}")
                time.sleep(self._param.delay_after_error)

        if last_e:
            self.set_output("_ERROR", str(last_e))
            return f"Google error: {last_e}"

        assert False, self.output()