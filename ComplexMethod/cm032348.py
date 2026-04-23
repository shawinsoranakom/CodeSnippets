def _invoke(self, **kwargs):
        if self.check_if_canceled("GitHub processing"):
            return

        if not kwargs.get("query"):
            self.set_output("formalized_content", "")
            return ""

        last_e = ""
        for _ in range(self._param.max_retries+1):
            if self.check_if_canceled("GitHub processing"):
                return

            try:
                url = 'https://api.github.com/search/repositories?q=' + kwargs["query"] + '&sort=stars&order=desc&per_page=' + str(
                    self._param.top_n)
                headers = {"Content-Type": "application/vnd.github+json", "X-GitHub-Api-Version": '2022-11-28'}
                response = requests.get(url=url, headers=headers).json()

                if self.check_if_canceled("GitHub processing"):
                    return

                self._retrieve_chunks(response['items'],
                                      get_title=lambda r: r["name"],
                                      get_url=lambda r: r["html_url"],
                                      get_content=lambda r: str(r["description"]) + '\n stars:' + str(r['watchers']))
                self.set_output("json", response['items'])
                return self.output("formalized_content")
            except Exception as e:
                if self.check_if_canceled("GitHub processing"):
                    return

                last_e = e
                logging.exception(f"GitHub error: {e}")
                time.sleep(self._param.delay_after_error)

        if last_e:
            self.set_output("_ERROR", str(last_e))
            return f"GitHub error: {last_e}"

        assert False, self.output()