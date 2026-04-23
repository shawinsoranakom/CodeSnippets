def _invoke(self, **kwargs):
        if self.check_if_canceled("UserFillUp processing"):
            return

        if self._param.enable_tips:
            content = self._param.tips
            for k, v in self.get_input_elements_from_text(self._param.tips).items():
                v = v["value"]
                ans = ""
                if isinstance(v, partial):
                    for t in v():
                        ans += t
                elif isinstance(v, list):
                    ans = ",".join([str(vv) for vv in v])
                elif not isinstance(v, str):
                    try:
                        ans = json.dumps(v, ensure_ascii=False)
                    except Exception:
                        pass
                else:
                    ans = v
                if not ans:
                    ans = ""
                content = re.sub(r"\{%s\}"%k, ans, content)

            self.set_output("tips", content)
        layout_recognize = self._param.layout_recognize or None
        for k, v in kwargs.get("inputs", {}).items():
            if self.check_if_canceled("UserFillUp processing"):
                return
            if isinstance(v, dict) and v.get("type", "").lower().find("file") >= 0:
                if v.get("optional") and v.get("value", None) is None:
                    v = None
                else:
                    file_value = v["value"]
                    # Support both single file (backward compatibility) and multiple files
                    files = file_value if isinstance(file_value, list) else [file_value]
                    v = FileService.get_files(files, layout_recognize=layout_recognize)
            else:
                v = v.get("value")
            self.set_output(k, v)