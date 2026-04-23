def signal_handler(signal_number, stack_frame):
        # The server will shut down its threads and exit its loop.
        server.stop()