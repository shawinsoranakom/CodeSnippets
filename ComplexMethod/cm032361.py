def _invoke(self, **kwargs):
        if self.check_if_canceled("SearXNG processing"):
            return

        # Gracefully handle try-run without inputs
        query = kwargs.get("query")
        if not query or not isinstance(query, str) or not query.strip():
            self.set_output("formalized_content", "")
            return ""

        searxng_url = (getattr(self._param, "searxng_url", "") or kwargs.get("searxng_url") or "").strip()
        # In try-run, if no URL configured, just return empty instead of raising
        if not searxng_url:
            self.set_output("formalized_content", "")
            return ""

        last_e = ""
        for _ in range(self._param.max_retries+1):
            if self.check_if_canceled("SearXNG processing"):
                return

            try:
                search_params = {
                    'q': query,
                    'format': 'json',
                    'categories': 'general',
                    'language': 'auto',
                    'safesearch': 1,
                    'pageno': 1
                }

                response = requests.get(
                    f"{searxng_url}/search",
                    params=search_params,
                    timeout=10
                )
                response.raise_for_status()

                if self.check_if_canceled("SearXNG processing"):
                    return

                data = response.json()

                if not data or not isinstance(data, dict):
                    raise ValueError("Invalid response from SearXNG")

                results = data.get("results", [])
                if not isinstance(results, list):
                    raise ValueError("Invalid results format from SearXNG")

                results = results[:self._param.top_n]

                if self.check_if_canceled("SearXNG processing"):
                    return

                self._retrieve_chunks(results,
                                      get_title=lambda r: r.get("title", ""),
                                      get_url=lambda r: r.get("url", ""),
                                      get_content=lambda r: r.get("content", ""))

                self.set_output("json", results)
                return self.output("formalized_content")

            except requests.RequestException as e:
                if self.check_if_canceled("SearXNG processing"):
                    return

                last_e = f"Network error: {e}"
                logging.exception(f"SearXNG network error: {e}")
                time.sleep(self._param.delay_after_error)
            except Exception as e:
                if self.check_if_canceled("SearXNG processing"):
                    return

                last_e = str(e)
                logging.exception(f"SearXNG error: {e}")
                time.sleep(self._param.delay_after_error)

        if last_e:
            self.set_output("_ERROR", last_e)
            return f"SearXNG error: {last_e}"

        assert False, self.output()