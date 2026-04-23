def _invoke(self, **kwargs):
        if self.check_if_canceled("WenCai processing"):
            return

        if not kwargs.get("query"):
            self.set_output("report", "")
            return ""

        last_e = ""
        for _ in range(self._param.max_retries+1):
            if self.check_if_canceled("WenCai processing"):
                return

            try:
                wencai_res = []
                # res = pywencai.get(query=kwargs["query"], query_type=self._param.query_type, perpage=self._param.top_n)
                res = []
                if self.check_if_canceled("WenCai processing"):
                    return

                if isinstance(res, pd.DataFrame):
                    wencai_res.append(res.to_markdown())
                elif isinstance(res, dict):
                    for item in res.items():
                        if self.check_if_canceled("WenCai processing"):
                            return

                        if isinstance(item[1], list):
                            wencai_res.append(item[0] + "\n" + pd.DataFrame(item[1]).to_markdown())
                        elif isinstance(item[1], str):
                            wencai_res.append(item[0] + "\n" + item[1])
                        elif isinstance(item[1], dict):
                            if "meta" in item[1].keys():
                                continue
                            wencai_res.append(pd.DataFrame.from_dict(item[1], orient='index').to_markdown())
                        elif isinstance(item[1], pd.DataFrame):
                            if "image_url" in item[1].columns:
                                continue
                            wencai_res.append(item[1].to_markdown())
                        else:
                            wencai_res.append(item[0] + "\n" + str(item[1]))
                self.set_output("report", "\n\n".join(wencai_res))
                return self.output("report")
            except Exception as e:
                if self.check_if_canceled("WenCai processing"):
                    return

                last_e = e
                logging.exception(f"WenCai error: {e}")
                time.sleep(self._param.delay_after_error)

        if last_e:
            self.set_output("_ERROR", str(last_e))
            return f"WenCai error: {last_e}"

        assert False, self.output()