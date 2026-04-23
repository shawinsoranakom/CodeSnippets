def request_headers(self, method: str, extra, request_id: Optional[str]) -> Dict[str, str]:
        user_agent = "LLM/v1 PythonBindings/%s" % (version.VERSION,)

        uname_without_node = " ".join(v for k, v in platform.uname()._asdict().items() if k != "node")
        ua = {
            "bindings_version": version.VERSION,
            "httplib": "requests",
            "lang": "python",
            "lang_version": platform.python_version(),
            "platform": platform.platform(),
            "publisher": "openai",
            "uname": uname_without_node,
        }

        headers = {
            "X-LLM-Client-User-Agent": json.dumps(ua),
            "User-Agent": user_agent,
        }
        if self.api_key:
            headers.update(api_key_to_header(self.api_type, self.api_key))

        if self.organization:
            headers["LLM-Organization"] = self.organization

        if self.api_version is not None and self.api_type == ApiType.OPEN_AI:
            headers["LLM-Version"] = self.api_version
        if request_id is not None:
            headers["X-Request-Id"] = request_id
        headers.update(extra)

        return headers