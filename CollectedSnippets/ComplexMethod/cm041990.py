async def _run_precheck(self, browser_type):
        if self._has_run_precheck:
            return

        executable_path = Path(browser_type.executable_path)
        if not executable_path.exists() and "executable_path" not in self.launch_kwargs:
            kwargs = {}
            if self.proxy:
                kwargs["env"] = {"ALL_PROXY": self.proxy}
            await _install_browsers(self.browser_type, **kwargs)

            if self._has_run_precheck:
                return

            if not executable_path.exists():
                parts = executable_path.parts
                available_paths = list(Path(*parts[:-3]).glob(f"{self.browser_type}-*"))
                if available_paths:
                    logger.warning(
                        "It seems that your OS is not officially supported by Playwright. "
                        "Try to set executable_path to the fallback build version."
                    )
                    executable_path = available_paths[0].joinpath(*parts[-2:])
                    self.launch_kwargs["executable_path"] = str(executable_path)
        self._has_run_precheck = True