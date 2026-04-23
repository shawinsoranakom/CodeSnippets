async def _execute_code_dont_check_setup(
        self, code_blocks: List[CodeBlock], cancellation_token: CancellationToken
    ) -> CodeResult:
        logs_all = ""
        exitcode = 0

        # TODO: Better to use the client auth system rather than headers
        assert self._access_token is not None
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }
        properties = {
            "codeInputType": "inline",
            "executionType": "synchronous",
            "code": "",  # Filled in later
        }
        url = self._construct_url("code/execute")
        timeout = aiohttp.ClientTimeout(total=float(self._timeout))
        async with aiohttp.ClientSession(timeout=timeout) as client:
            for code_block in code_blocks:
                lang, code = code_block.language, code_block.code
                lang = lang.lower()

                if lang in PYTHON_VARIANTS:
                    lang = "python"

                if lang not in self.SUPPORTED_LANGUAGES:
                    # In case the language is not supported, we return an error message.
                    exitcode = 1
                    logs_all += "\n" + f"unknown language {lang}"
                    break

                if self._available_packages is not None:
                    req_pkgs = get_required_packages(code, lang)
                    missing_pkgs = set(req_pkgs - self._available_packages)
                    if len(missing_pkgs) > 0:
                        # In case the code requires packages that are not available in the environment
                        exitcode = 1
                        logs_all += "\n" + f"Python packages unavailable in environment: {missing_pkgs}"
                        break

                properties["code"] = code_block.code

                task = asyncio.create_task(
                    client.post(
                        url,
                        headers=headers,
                        json={"properties": properties},
                    )
                )

                cancellation_token.link_future(task)
                try:
                    response = await task
                    response.raise_for_status()
                    data = await response.json()
                    data = data["properties"]
                    logs_all += data.get("stderr", "") + data.get("stdout", "")
                    if "Success" in data["status"]:
                        if not self._suppress_result_output:
                            logs_all += str(data["result"])
                    elif "Failure" in data["status"]:
                        exitcode = 1

                except asyncio.TimeoutError as e:
                    logs_all += "\n Timeout"
                    # e.add_note is only in py 3.11+
                    raise asyncio.TimeoutError(logs_all) from e
                except asyncio.CancelledError as e:
                    logs_all += "\n Cancelled"
                    # e.add_note is only in py 3.11+
                    raise asyncio.CancelledError(logs_all) from e
                except aiohttp.ClientResponseError as e:
                    logs_all += "\nError while sending code block to endpoint"
                    raise ConnectionError(logs_all) from e

        return CodeResult(exit_code=exitcode, output=logs_all)