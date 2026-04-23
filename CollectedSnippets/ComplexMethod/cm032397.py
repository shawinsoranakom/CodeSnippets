def _invoke(self, **kwargs):
        if self.check_if_canceled("Begin processing"):
            return

        layout_recognize = self._param.layout_recognize or None
        for k, v in kwargs.get("inputs", {}).items():
            if self.check_if_canceled("Begin processing"):
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
            self.set_input_value(k, v)