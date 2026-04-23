async def check_server(server_name: str) -> dict:
        server_info: dict[str, str | int | None] = {"name": server_name, "mode": None, "toolsCount": None}
        # Create clients that we control so we can clean them up after
        mcp_stdio_client = MCPStdioClient()
        mcp_streamable_http_client = MCPStreamableHttpClient()
        try:
            # Get global variables from database for header resolution
            request_variables = {}
            try:
                from sqlmodel import select

                from langflow.services.auth import utils as auth_utils
                from langflow.services.database.models.variable.model import Variable

                # Load variables directly from database and decrypt ALL types (including CREDENTIAL)
                stmt = select(Variable).where(Variable.user_id == current_user.id)
                variables = list((await session.exec(stmt)).all())

                # Decrypt variables based on type (following the pattern from get_all_decrypted_variables)
                for variable in variables:
                    if variable.name and variable.value:
                        # Prior to v1.8, both Generic and Credential variables were encrypted.
                        # As such, must attempt to decrypt both types to ensure backwards-compatibility.
                        try:
                            decrypted_value = auth_utils.decrypt_api_key(variable.value)
                            request_variables[variable.name] = decrypted_value
                        except Exception as e:  # noqa: BLE001
                            await logger.aerror(
                                f"Failed to decrypt credential variable '{variable.name}': {e}. "
                                "This credential will not be available for MCP server."
                            )
            except Exception as e:  # noqa: BLE001
                await logger.awarning(f"Failed to load global variables for MCP server test: {e}")

            mode, tool_list, _ = await update_tools(
                server_name=server_name,
                server_config=server_list["mcpServers"][server_name],
                mcp_stdio_client=mcp_stdio_client,
                mcp_streamable_http_client=mcp_streamable_http_client,
                request_variables=request_variables,
            )
            server_info["mode"] = mode.lower()
            server_info["toolsCount"] = len(tool_list)
            if len(tool_list) == 0:
                server_info["error"] = "No tools found"
        except ValueError as e:
            # Configuration validation errors, invalid URLs, etc.
            await logger.aerror(f"Configuration error for server {server_name}: {e}")
            server_info["error"] = f"Configuration error: {e}"
        except ConnectionError as e:
            # Network connection and timeout issues
            await logger.aerror(f"Connection error for server {server_name}: {e}")
            server_info["error"] = f"Connection failed: {e}"
        except (TimeoutError, asyncio.TimeoutError) as e:
            # Timeout errors
            await logger.aerror(f"Timeout error for server {server_name}: {e}")
            server_info["error"] = "Timeout when checking server tools"
        except OSError as e:
            # System-level errors (process execution, file access)
            await logger.aerror(f"System error for server {server_name}: {e}")
            server_info["error"] = f"System error: {e}"
        except (KeyError, TypeError) as e:
            # Data parsing and access errors
            await logger.aerror(f"Data error for server {server_name}: {e}")
            server_info["error"] = f"Configuration data error: {e}"
        except (RuntimeError, ProcessLookupError, PermissionError) as e:
            # Runtime and process-related errors
            await logger.aerror(f"Runtime error for server {server_name}: {e}")
            server_info["error"] = f"Runtime error: {e}"
        except Exception as e:  # noqa: BLE001
            # Generic catch-all for other exceptions (including ExceptionGroup)
            if hasattr(e, "exceptions") and e.exceptions:
                # Extract the first underlying exception for a more meaningful error message
                underlying_error = e.exceptions[0]
                if hasattr(underlying_error, "exceptions"):
                    await logger.aerror(
                        f"Error checking server {server_name}: {underlying_error}, {underlying_error.exceptions}"
                    )
                    underlying_error = underlying_error.exceptions[0]
                else:
                    await logger.aexception(f"Error checking server {server_name}: {underlying_error}")
                server_info["error"] = f"Error loading server: {underlying_error}"
            else:
                await logger.aexception(f"Error checking server {server_name}: {e}")
                server_info["error"] = f"Error loading server: {e}"
        finally:
            # Always disconnect clients to prevent mcp-proxy process leaks
            # These clients spawn subprocesses that need to be explicitly terminated
            await mcp_stdio_client.disconnect()
            await mcp_streamable_http_client.disconnect()
        return server_info