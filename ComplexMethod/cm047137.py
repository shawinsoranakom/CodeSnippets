def _open_websocket(self):
        version = self._json_command('version')
        self._logger.info('Browser version: %s', version['Browser'])

        start = time.time()
        while (time.time() - start) < 5.0:
            ws_url = next((
                target['webSocketDebuggerUrl']
                for target in self._json_command('')
                if target['type'] == 'page'
                if target['url'] == 'about:blank'
            ), None)
            if ws_url:
                break

            time.sleep(0.1)
        else:
            self.stop()
            raise unittest.SkipTest("Error during Chrome connection: never found 'page' target")

        self._logger.info('Websocket url found: %s', ws_url)
        ws = websocket.create_connection(ws_url, enable_multithread=True, suppress_origin=True)
        if ws.getstatus() != 101:
            raise unittest.SkipTest("Cannot connect to chrome dev tools")
        ws.settimeout(0.01)
        try:
            yield ws
        finally:
            self._logger.info("Closing websocket connection")
            ws.close()