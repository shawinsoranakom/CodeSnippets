async def execute_code_blocks(
        self, code_blocks: List[CodeBlock], cancellation_token: CancellationToken
    ) -> DockerJupyterCodeResult:
        """(Experimental) Execute a list of code blocks and return the result.

        This method executes a list of code blocks as cells in the Jupyter kernel.
        See: https://jupyter-client.readthedocs.io/en/stable/messaging.html
        for the message protocol.

        Args:
            code_blocks (List[CodeBlock]): A list of code blocks to execute.

        Returns:
            DockerJupyterCodeResult: The result of the code execution.
        """
        kernel_client = await self._ensure_async_kernel_client()
        # Wait for kernel to be ready using async client
        is_ready = await kernel_client.wait_for_ready(timeout_seconds=self._timeout)
        if not is_ready:
            return DockerJupyterCodeResult(exit_code=1, output="ERROR: Kernel not ready", output_files=[])

        outputs: List[str] = []
        output_files: List[Path] = []
        for code_block in code_blocks:
            code = silence_pip(code_block.code, code_block.language)
            # Execute code using async client
            exec_task = asyncio.create_task(kernel_client.execute(code, timeout_seconds=self._timeout))
            cancellation_token.link_future(exec_task)
            result = await exec_task
            if result.is_ok:
                outputs.append(result.output)
                for data in result.data_items:
                    if data.mime_type == "image/png":
                        path = self._save_image(data.data)
                        outputs.append(path)
                        output_files.append(Path(path))
                    elif data.mime_type == "text/html":
                        path = self._save_html(data.data)
                        outputs.append(path)
                        output_files.append(Path(path))
                    else:
                        outputs.append(json.dumps(data.data))
            else:
                existing_output = "\n".join([str(output) for output in outputs])
                return DockerJupyterCodeResult(
                    exit_code=1, output=existing_output + "\nERROR: " + result.output, output_files=output_files
                )
        return DockerJupyterCodeResult(
            exit_code=0, output="\n".join([str(output) for output in outputs]), output_files=output_files
        )