async def handle_request(self, request: MCPRequest) -> MCPResponse:
        """Handle incoming MCP request"""
        try:
            method = request.method
            params = request.params or {}

            # Handle MCP protocol methods
            if method == "initialize":
                result = {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": self.server_info,
                    "capabilities": {
                        "tools": {}
                    }
                }
                return MCPResponse(jsonrpc="2.0", id=request.id, result=result)

            elif method == "tools/list":
                result = {
                    "tools": self.get_tool_list()
                }
                return MCPResponse(jsonrpc="2.0", id=request.id, result=result)

            elif method == "tools/call":
                tool_name = params.get("name")
                tool_arguments = params.get("arguments", {})
                tool_arguments.setdefault("origin", request.origin)

                if tool_name not in self.tools:
                    return MCPResponse(
                        jsonrpc="2.0",
                        id=request.id,
                        error={
                            "code": -32601,
                            "message": f"Tool not found: {tool_name}"
                        }
                    )

                tool = self.tools[tool_name]
                result = await tool.execute(tool_arguments)

                return MCPResponse(
                    jsonrpc="2.0",
                    id=request.id,
                    result=result
                )

            elif method == "ping":
                return MCPResponse(jsonrpc="2.0", id=request.id, result={})

            else:
                return MCPResponse(
                    jsonrpc="2.0",
                    id=request.id,
                    error={
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                )

        except Exception as e:
            return MCPResponse(
                jsonrpc="2.0",
                id=request.id,
                error={
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            )