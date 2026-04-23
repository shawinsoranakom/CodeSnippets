async def _setup_functions(self, cancellation_token: CancellationToken) -> None:
        if not self._func_code:
            self._func_code = build_python_functions_file(self._functions)

            # Check required function imports and packages
            lists_of_packages = [x.python_packages for x in self._functions if isinstance(x, FunctionWithRequirements)]
            # Should we also be checking the imports?

            flattened_packages = [item for sublist in lists_of_packages for item in sublist]
            required_packages = set(flattened_packages)

            if self._available_packages is None:
                await self._populate_available_packages(cancellation_token)

            if self._available_packages is not None:
                missing_pkgs = set(required_packages - self._available_packages)
                if len(missing_pkgs) > 0:
                    raise ValueError(f"Packages unavailable in environment: {missing_pkgs}")

        func_file = self.work_dir / f"{self._functions_module}.py"
        func_file.write_text(self._func_code)

        # Attempt to load the function file to check for syntax errors, imports etc.
        exec_result = await self._execute_code_dont_check_setup(
            [CodeBlock(code=self._func_code, language="python")], cancellation_token
        )

        if exec_result.exit_code != 0:
            raise ValueError(f"Functions failed to load: {exec_result.output.strip()}")

        self._setup_functions_complete = True