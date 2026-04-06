async def openapi(req: Request) -> JSONResponse:
                root_path = req.scope.get("root_path", "").rstrip("/")
                schema = self.openapi()
                if root_path and self.root_path_in_servers:
                    server_urls = {s.get("url") for s in schema.get("servers", [])}
                    if root_path not in server_urls:
                        schema = dict(schema)
                        schema["servers"] = [{"url": root_path}] + schema.get(
                            "servers", []
                        )
                return JSONResponse(schema)