async def get_browser_state(self) -> Optional[dict]:
        browser_tool = self.agent.available_tools.get_tool(BrowserUseTool().name)
        if not browser_tool:
            browser_tool = self.agent.available_tools.get_tool(
                SandboxBrowserTool().name
            )
        if not browser_tool or not hasattr(browser_tool, "get_current_state"):
            logger.warning("BrowserUseTool not found or doesn't have get_current_state")
            return None
        try:
            result = await browser_tool.get_current_state()
            if result.error:
                logger.debug(f"Browser state error: {result.error}")
                return None
            if hasattr(result, "base64_image") and result.base64_image:
                self._current_base64_image = result.base64_image
            else:
                self._current_base64_image = None
            return json.loads(result.output)
        except Exception as e:
            logger.debug(f"Failed to get browser state: {str(e)}")
            return None