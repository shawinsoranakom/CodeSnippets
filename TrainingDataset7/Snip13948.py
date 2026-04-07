def _terminate_thread(cls):
        # Terminate the live server's thread.
        cls.server_thread.terminate()
        # Restore shared connections' non-shareability.
        for conn in cls.server_thread.connections_override.values():
            conn.dec_thread_sharing()