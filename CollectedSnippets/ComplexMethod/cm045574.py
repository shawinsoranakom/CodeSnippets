async def _execute_browser_action(
        self, endpoint: str, params: dict = None, method: str = "POST"
    ) -> ToolResult:
        """Execute a browser automation action through the sandbox API."""
        try:
            await self._ensure_sandbox()
            url = f"http://localhost:8003/api/automation/{endpoint}"
            if method == "GET" and params:
                query_params = "&".join([f"{k}={v}" for k, v in params.items()])
                url = f"{url}?{query_params}"
                curl_cmd = (
                    f"curl -s -X {method} '{url}' -H 'Content-Type: application/json'"
                )
            else:
                curl_cmd = (
                    f"curl -s -X {method} '{url}' -H 'Content-Type: application/json'"
                )
                if params:
                    json_data = json.dumps(params)
                    curl_cmd += f" -d '{json_data}'"
            logger.debug(f"Executing curl command: {curl_cmd}")
            response = self.sandbox.process.exec(curl_cmd, timeout=30)
            if response.exit_code == 0:
                try:
                    result = json.loads(response.result)
                    result.setdefault("content", "")
                    result.setdefault("role", "assistant")
                    if "screenshot_base64" in result:
                        screenshot_data = result["screenshot_base64"]
                        is_valid, validation_message = self._validate_base64_image(
                            screenshot_data
                        )
                        if not is_valid:
                            logger.warning(
                                f"Screenshot validation failed: {validation_message}"
                            )
                            result["image_validation_error"] = validation_message
                            del result["screenshot_base64"]

                    # added_message = await self.thread_manager.add_message(
                    #     thread_id=self.thread_id,
                    #     type="browser_state",
                    #     content=result,
                    #     is_llm_message=False
                    # )
                    message = ThreadMessage(
                        type="browser_state", content=result, is_llm_message=False
                    )
                    self.browser_message = message
                    success_response = {
                        "success": result.get("success", False),
                        "message": result.get("message", "Browser action completed"),
                    }
                    #         if added_message and 'message_id' in added_message:
                    #             success_response['message_id'] = added_message['message_id']
                    for field in [
                        "url",
                        "title",
                        "element_count",
                        "pixels_below",
                        "ocr_text",
                        "image_url",
                    ]:
                        if field in result:
                            success_response[field] = result[field]
                    return (
                        self.success_response(success_response)
                        if success_response["success"]
                        else self.fail_response(success_response)
                    )
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse response JSON: {e}")
                    return self.fail_response(f"Failed to parse response JSON: {e}")
            else:
                logger.error(f"Browser automation request failed: {response}")
                return self.fail_response(
                    f"Browser automation request failed: {response}"
                )
        except Exception as e:
            logger.error(f"Error executing browser action: {e}")
            logger.debug(traceback.format_exc())
            return self.fail_response(f"Error executing browser action: {e}")