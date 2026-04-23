def _run_script_thread(self) -> None:
        try:
            super()._run_script_thread()
        except BaseException as e:
            self.script_thread_exceptions.append(e)