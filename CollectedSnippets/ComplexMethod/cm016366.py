async def websocket_handler(request):
            ws = web.WebSocketResponse()
            await ws.prepare(request)
            sid = request.rel_url.query.get('clientId', '')
            if sid:
                # Reusing existing session, remove old
                self.sockets.pop(sid, None)
            else:
                sid = uuid.uuid4().hex

            # Store WebSocket for backward compatibility
            self.sockets[sid] = ws
            # Store metadata separately
            self.sockets_metadata[sid] = {"feature_flags": {}}

            try:
                # Send initial state to the new client
                await self.send("status", {"status": self.get_queue_info(), "sid": sid}, sid)
                # On reconnect if we are the currently executing client send the current node
                if self.client_id == sid and self.last_node_id is not None:
                    await self.send("executing", { "node": self.last_node_id }, sid)

                # Flag to track if we've received the first message
                first_message = True

                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.ERROR:
                        logging.warning('ws connection closed with exception %s' % ws.exception())
                    elif msg.type == aiohttp.WSMsgType.TEXT:
                        try:
                            data = json.loads(msg.data)
                            # Check if first message is feature flags
                            if first_message and data.get("type") == "feature_flags":
                                # Store client feature flags
                                client_flags = data.get("data", {})
                                self.sockets_metadata[sid]["feature_flags"] = client_flags

                                # Send server feature flags in response
                                await self.send(
                                    "feature_flags",
                                    feature_flags.get_server_features(),
                                    sid,
                                )

                                logging.debug(
                                    f"Feature flags negotiated for client {sid}: {client_flags}"
                                )
                            first_message = False
                        except json.JSONDecodeError:
                            logging.warning(
                                f"Invalid JSON received from client {sid}: {msg.data}"
                            )
                        except Exception as e:
                            logging.error(f"Error processing WebSocket message: {e}")
            finally:
                self.sockets.pop(sid, None)
                self.sockets_metadata.pop(sid, None)
            return ws