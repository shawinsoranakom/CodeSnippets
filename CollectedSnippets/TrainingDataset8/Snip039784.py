async def _check_script_loading(
        self, script: str, expected_loads: bool, expected_msg: str
    ) -> None:
        with os.fdopen(self._fd, "w") as tmp:
            tmp.write(script)

        ok, msg = await self.runtime.does_script_run_without_error()
        event_based_path_watcher._MultiPathWatcher.get_singleton().close()
        event_based_path_watcher._MultiPathWatcher._singleton = None
        self.assertEqual(expected_loads, ok)
        self.assertEqual(expected_msg, msg)