async def _setup_functions(self, cancellation_token: CancellationToken) -> None:
        func_file_content = build_python_functions_file(self._functions)
        func_file = self.work_dir / f"{self._functions_module}.py"
        func_file.write_text(func_file_content)

        # Collect requirements
        lists_of_packages = [x.python_packages for x in self._functions if isinstance(x, FunctionWithRequirements)]
        flattened_packages = [item for sublist in lists_of_packages for item in sublist]
        required_packages = list(set(flattened_packages))
        if len(required_packages) > 0:
            logging.info("Ensuring packages are installed in executor.")

            cmd_args = ["-m", "pip", "install"]
            cmd_args.extend(required_packages)

            if self._virtual_env_context:
                py_executable = self._virtual_env_context.env_exe
            else:
                py_executable = sys.executable

            task = asyncio.create_task(
                asyncio.create_subprocess_exec(
                    py_executable,
                    *cmd_args,
                    cwd=self.work_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
            )
            cancellation_token.link_future(task)
            try:
                proc = await task
                stdout, stderr = await asyncio.wait_for(proc.communicate(), self._timeout)
            except asyncio.TimeoutError as e:
                raise ValueError("Pip install timed out") from e
            except asyncio.CancelledError as e:
                raise ValueError("Pip install was cancelled") from e

            if proc.returncode is not None and proc.returncode != 0:
                raise ValueError(f"Pip install failed. {stdout.decode()}, {stderr.decode()}")

        # Attempt to load the function file to check for syntax errors, imports etc.
        exec_result = await self._execute_code_dont_check_setup(
            [CodeBlock(code=func_file_content, language="python")], cancellation_token
        )

        if exec_result.exit_code != 0:
            raise ValueError(f"Functions failed to load: {exec_result.output}")

        self._setup_functions_complete = True