def _receive(self, dbname):
        threading.current_thread().dbname = dbname
        # So CDT uses a streamed JSON-RPC structure, meaning a request is
        # {id, method, params} and eventually a {id, result | error} should
        # arrive the other way, however for events it uses "notifications"
        # meaning request objects without an ``id``, but *coming from the server
        while True: # or maybe until `self._result` is `done()`?
            try:
                msg = self.ws.recv()
                if not msg:
                    continue
                self._logger.debug('\n<- %s', msg)
            except websocket.WebSocketTimeoutException:
                continue
            except websocket.WebSocketConnectionClosedException as e:
                if not self._result.done():
                    del self.ws
                    self._result.set_exception(e)
                    while True:
                        try:
                            _, f = self._responses.popitem()
                        except KeyError:
                            break
                        else:
                            f.cancel()
                return
            except Exception as e:
                if isinstance(e, ConnectionResetError) and self._result.done():
                    return
                # if the socket is still connected something bad happened,
                # otherwise the client was just shut down
                if self.ws.connected:
                    self._result.set_exception(e)
                    raise
                self._result.cancel()
                return

            res = json.loads(msg)
            request_id = res.get('id')
            try:
                if request_id is None:
                    if handler := self._handlers.get(res['method']):
                        handler(**res['params'])
                elif f := self._responses.pop(request_id, None):
                    if 'result' in res:
                        f.set_result(res['result'])
                    else:
                        f.set_exception(ChromeBrowserException(res['error']['message']))
            except Exception:
                _logger.exception(
                    "While processing message %s",
                    shorten(str(msg), 500, placeholder='...'),
                )