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

            packages = shlex.join(required_packages)

            result = await self._execute_code_dont_check_setup(
                [CodeBlock(code=f"python -m pip install {packages}", language="sh")], cancellation_token
            )

            if result.exit_code != 0:
                stdout = result.output
                stderr = result.output
                raise ValueError(f"Pip install failed. {stdout}, {stderr}")

        # Attempt to load the function file to check for syntax errors, imports etc.
        exec_result = await self._execute_code_dont_check_setup(
            [CodeBlock(code=func_file_content, language="python")], cancellation_token
        )

        if exec_result.exit_code != 0:
            raise ValueError(f"Functions failed to load: {exec_result.output}")

        self._setup_functions_complete = True