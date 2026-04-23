def _serve_forever(cls, websocket, db, httprequest, version):
        """
        Process incoming messages and dispatch them to the application.
        """
        current_thread = threading.current_thread()
        current_thread.type = 'websocket'
        if httprequest.user_agent and version != cls._VERSION:
            # Close the connection from an outdated worker. We can't use a
            # custom close code because the connection is considered successful,
            # preventing exponential reconnect backoff. This would cause old
            # workers to reconnect frequently, putting pressure on the server.
            # Clean closes don't trigger reconnections, assuming they are
            # intentional. The reason indicates to the origin worker not to
            # reconnect, preventing old workers from lingering after updates.
            # Non browsers are ignored since IOT devices do not provide the
            # worker version.
            websocket.close(CloseCode.CLEAN, "OUTDATED_VERSION")
        for message in websocket.get_messages():
            if message == b'\x00':
                # Ignore internal sentinel message used to detect dead/idle connections.
                continue
            with WebsocketRequest(db, httprequest, websocket) as req:
                try:
                    req.serve_websocket_message(message)
                except SessionExpiredException:
                    websocket.close(CloseCode.SESSION_EXPIRED)
                except PoolError:
                    websocket.close(CloseCode.TRY_LATER)
                except Exception:
                    _logger.exception("Exception occurred during websocket request handling")