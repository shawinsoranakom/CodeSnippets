async def _execute_code_dont_check_setup(
        self, code_blocks: List[CodeBlock], cancellation_token: CancellationToken
    ) -> CommandLineCodeResult:
        if self._container is None or not self._running:
            raise ValueError("Container is not running. Must first be started with either start or a context manager.")

        if len(code_blocks) == 0:
            raise ValueError("No code blocks to execute.")

        outputs: List[str] = []
        files: List[Path] = []
        last_exit_code = 0
        try:
            for code_block in code_blocks:
                lang = code_block.language.lower()
                code = silence_pip(code_block.code, lang)

                # Check if there is a filename comment
                try:
                    filename = get_file_name_from_content(code, self.work_dir)
                except ValueError:
                    outputs.append("Filename is not in the workspace")
                    last_exit_code = 1
                    break

                if not filename:
                    filename = f"tmp_code_{sha256(code.encode()).hexdigest()}.{lang}"

                code_path = self.work_dir / filename
                with code_path.open("w", encoding="utf-8") as fout:
                    fout.write(code)
                files.append(code_path)

                command = ["timeout", str(self._timeout), lang_to_cmd(lang), filename]

                output, exit_code = await self._execute_command(command, cancellation_token)
                outputs.append(output)
                last_exit_code = exit_code
                if exit_code != 0:
                    break
        finally:
            if self._delete_tmp_files:
                for file in files:
                    try:
                        file.unlink()
                    except (OSError, FileNotFoundError):
                        pass

        code_file = str(files[0]) if files else None
        return CommandLineCodeResult(exit_code=last_exit_code, output="".join(outputs), code_file=code_file)