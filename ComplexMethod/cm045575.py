async def execute(
        self,
        action: str,
        url: Optional[str] = None,
        index: Optional[int] = None,
        text: Optional[str] = None,
        amount: Optional[int] = None,
        page_id: Optional[int] = None,
        keys: Optional[str] = None,
        seconds: Optional[int] = None,
        x: Optional[int] = None,
        y: Optional[int] = None,
        element_source: Optional[str] = None,
        element_target: Optional[str] = None,
        **kwargs,
    ) -> ToolResult:
        """
        Execute a browser action in the sandbox environment.
        Args:
            action: The browser action to perform
            url: URL for navigation
            index: Element index for interaction
            text: Text for input or scroll actions
            amount: Pixel amount to scroll
            page_id: Tab ID for tab management
            keys: Keys to send for keyboard actions
            seconds: Seconds to wait
            x: X coordinate for click/drag
            y: Y coordinate for click/drag
            element_source: Source element for drag and drop
            element_target: Target element for drag and drop
        Returns:
            ToolResult with the action's output or error
        """
        # async with self.lock:
        try:
            # Navigation actions
            if action == "navigate_to":
                if not url:
                    return self.fail_response("URL is required for navigation")
                return await self._execute_browser_action("navigate_to", {"url": url})
            elif action == "go_back":
                return await self._execute_browser_action("go_back", {})
                # Interaction actions
            elif action == "click_element":
                if index is None:
                    return self.fail_response("Index is required for click_element")
                return await self._execute_browser_action(
                    "click_element", {"index": index}
                )
            elif action == "input_text":
                if index is None or not text:
                    return self.fail_response(
                        "Index and text are required for input_text"
                    )
                return await self._execute_browser_action(
                    "input_text", {"index": index, "text": text}
                )
            elif action == "send_keys":
                if not keys:
                    return self.fail_response("Keys are required for send_keys")
                return await self._execute_browser_action("send_keys", {"keys": keys})
                # Tab management
            elif action == "switch_tab":
                if page_id is None:
                    return self.fail_response("Page ID is required for switch_tab")
                return await self._execute_browser_action(
                    "switch_tab", {"page_id": page_id}
                )
            elif action == "close_tab":
                if page_id is None:
                    return self.fail_response("Page ID is required for close_tab")
                return await self._execute_browser_action(
                    "close_tab", {"page_id": page_id}
                )
                # Scrolling actions
            elif action == "scroll_down":
                params = {"amount": amount} if amount is not None else {}
                return await self._execute_browser_action("scroll_down", params)
            elif action == "scroll_up":
                params = {"amount": amount} if amount is not None else {}
                return await self._execute_browser_action("scroll_up", params)
            elif action == "scroll_to_text":
                if not text:
                    return self.fail_response("Text is required for scroll_to_text")
                return await self._execute_browser_action(
                    "scroll_to_text", {"text": text}
                )
            # Dropdown actions
            elif action == "get_dropdown_options":
                if index is None:
                    return self.fail_response(
                        "Index is required for get_dropdown_options"
                    )
                return await self._execute_browser_action(
                    "get_dropdown_options", {"index": index}
                )
            elif action == "select_dropdown_option":
                if index is None or not text:
                    return self.fail_response(
                        "Index and text are required for select_dropdown_option"
                    )
                return await self._execute_browser_action(
                    "select_dropdown_option", {"index": index, "text": text}
                )
                # Coordinate-based actions
            elif action == "click_coordinates":
                if x is None or y is None:
                    return self.fail_response(
                        "X and Y coordinates are required for click_coordinates"
                    )
                return await self._execute_browser_action(
                    "click_coordinates", {"x": x, "y": y}
                )
            elif action == "drag_drop":
                if not element_source or not element_target:
                    return self.fail_response(
                        "Source and target elements are required for drag_drop"
                    )
                return await self._execute_browser_action(
                    "drag_drop",
                    {
                        "element_source": element_source,
                        "element_target": element_target,
                    },
                )
            # Utility actions
            elif action == "wait":
                seconds_to_wait = seconds if seconds is not None else 3
                return await self._execute_browser_action(
                    "wait", {"seconds": seconds_to_wait}
                )
            else:
                return self.fail_response(f"Unknown action: {action}")
        except Exception as e:
            logger.error(f"Error executing browser action: {e}")
            return self.fail_response(f"Error executing browser action: {e}")