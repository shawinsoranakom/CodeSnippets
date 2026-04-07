def run_live_server_thread(self, connections_override=None):
        thread = LiveServerTestCase._create_server_thread(connections_override)
        thread.daemon = True
        thread.start()
        thread.is_ready.wait()
        thread.terminate()