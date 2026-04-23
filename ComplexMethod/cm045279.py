async def _execute_code_block(
        self, code_block: CodeBlock, cancellation_token: CancellationToken
    ) -> JupyterCodeResult:
        """Execute single code block and return the result.

        Args:
            code_block (CodeBlock): The code block to execute.

        Returns:
            JupyterCodeResult: The result of the code execution.
        """
        execute_task = asyncio.create_task(
            self._execute_cell(
                nbformat.new_code_cell(silence_pip(code_block.code, code_block.language))  # type: ignore
            )
        )

        cancellation_token.link_future(execute_task)
        output_cell = await asyncio.wait_for(asyncio.shield(execute_task), timeout=self._timeout)

        outputs: list[str] = []
        output_files: list[Path] = []
        exit_code = 0

        for output in output_cell.get("outputs", []):
            match output.get("output_type"):
                case "stream":
                    outputs.append(output.get("text", ""))
                case "error":
                    traceback = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", "\n".join(output["traceback"]))
                    outputs.append(traceback)
                    exit_code = 1
                case "execute_result" | "display_data":
                    data = output.get("data", {})
                    for mime, content in data.items():
                        match mime:
                            case "text/plain":
                                outputs.append(content)
                            case "image/png":
                                path = self._save_image(content)
                                output_files.append(path)
                            case "image/jpeg":
                                # TODO: Should this also be encoded? Images are encoded as both png and jpg
                                pass
                            case "text/html":
                                path = self._save_html(content)
                                output_files.append(path)
                            case _:
                                outputs.append(json.dumps(content))
                case _:
                    pass

        return JupyterCodeResult(exit_code=exit_code, output="\n".join(outputs), output_files=output_files)