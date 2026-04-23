async def _validate_session_connectivity(self, session) -> bool:
        """Validate that the session is actually usable by testing a simple operation."""
        try:
            # Try to list tools as a connectivity test (this is a lightweight operation)
            # Use a shorter timeout for the connectivity test to fail fast
            response = await asyncio.wait_for(session.list_tools(), timeout=3.0)
        except (asyncio.TimeoutError, ConnectionError, OSError, ValueError) as e:
            await logger.adebug(f"Session connectivity test failed (standard error): {e}")
            return False
        except Exception as e:
            # Handle MCP-specific errors that might not be in the standard list
            error_str = str(e)
            if (
                "ClosedResourceError" in str(type(e))
                or "Connection closed" in error_str
                or "Connection lost" in error_str
                or "Connection failed" in error_str
                or "Transport closed" in error_str
                or "Stream closed" in error_str
            ):
                await logger.adebug(f"Session connectivity test failed (MCP connection error): {e}")
                return False
            # Re-raise unexpected errors
            await logger.awarning(f"Unexpected error in connectivity test: {e}")
            raise
        else:
            # Validate that we got a meaningful response
            if response is None:
                await logger.adebug("Session connectivity test failed: received None response")
                return False
            try:
                # Check if we can access the tools list (even if empty)
                tools = getattr(response, "tools", None)
                if tools is None:
                    await logger.adebug("Session connectivity test failed: no tools attribute in response")
                    return False
            except (AttributeError, TypeError) as e:
                await logger.adebug(f"Session connectivity test failed while validating response: {e}")
                return False
            else:
                await logger.adebug(f"Session connectivity test passed: found {len(tools)} tools")
                return True