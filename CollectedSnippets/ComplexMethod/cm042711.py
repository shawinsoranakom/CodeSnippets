def _add_middleware(self, mw: Any) -> None:
        if hasattr(mw, "process_spider_input"):
            self.methods["process_spider_input"].append(mw.process_spider_input)
            self._check_mw_method_spider_arg(mw.process_spider_input)

        if self._use_start_requests:
            if hasattr(mw, "process_start_requests"):
                self.methods["process_start_requests"].appendleft(
                    mw.process_start_requests
                )
        elif hasattr(mw, "process_start"):
            self.methods["process_start"].appendleft(mw.process_start)

        process_spider_output = self._get_async_method_pair(mw, "process_spider_output")
        self.methods["process_spider_output"].appendleft(process_spider_output)
        if callable(process_spider_output):
            self._check_mw_method_spider_arg(process_spider_output)
        elif isinstance(process_spider_output, tuple):
            for m in process_spider_output:
                self._check_mw_method_spider_arg(m)

        process_spider_exception = getattr(mw, "process_spider_exception", None)
        self.methods["process_spider_exception"].appendleft(process_spider_exception)
        if process_spider_exception is not None:
            self._check_mw_method_spider_arg(process_spider_exception)