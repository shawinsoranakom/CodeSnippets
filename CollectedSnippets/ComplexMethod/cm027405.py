async def _async_update_data(self) -> list[llm.Tool]:
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            async with asyncio.timeout(TIMEOUT):
                async with mcp_client(
                    self.hass, self.config_entry.data[CONF_URL], self.token_manager
                ) as session:
                    result = await session.list_tools()
        except TimeoutError as error:
            _LOGGER.debug("Timeout when listing tools: %s", error)
            raise UpdateFailed(f"Timeout when listing tools: {error}") from error
        except httpx.HTTPStatusError as error:
            _LOGGER.debug("Error communicating with API: %s", error)
            if error.response.status_code == 401 and self.token_manager is not None:
                raise ConfigEntryAuthFailed(
                    "The MCP server requires authentication"
                ) from error
            raise UpdateFailed(f"Error communicating with API: {error}") from error
        except httpx.HTTPError as err:
            _LOGGER.debug("Error communicating with API: %s", err)
            raise UpdateFailed(f"Error communicating with API: {err}") from err

        _LOGGER.debug("Received tools: %s", result.tools)
        tools: list[llm.Tool] = []
        for tool in result.tools:
            try:
                parameters = convert_to_voluptuous(tool.inputSchema)
            except Exception as err:
                raise UpdateFailed(
                    f"Error converting schema {err}: {tool.inputSchema}"
                ) from err
            tools.append(
                ModelContextProtocolTool(
                    tool.name,
                    tool.description,
                    parameters,
                    self.config_entry.data[CONF_URL],
                    self.token_manager,
                )
            )
        return tools