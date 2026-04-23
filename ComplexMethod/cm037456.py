def __call__(self):
        """Clean up background resources."""

        self.engine_dead = True
        if self.engine_manager is not None:
            self.engine_manager.shutdown()
        if self.coordinator is not None:
            self.coordinator.shutdown()

        if isinstance(self.output_socket, zmq.asyncio.Socket):
            # Async case.
            loop = self.output_queue_task._loop if self.output_queue_task else None

            sockets = (
                self.output_socket,
                self.input_socket,
                self.first_req_send_socket,
                self.first_req_rcv_socket,
                self.stats_update_socket,
            )

            tasks = (self.output_queue_task, self.stats_update_task)

            def close_sockets_and_tasks():
                close_sockets(sockets)
                for task in tasks:
                    if task is not None and not task.done():
                        with contextlib.suppress(Exception):
                            task.cancel()

            if loop is not None:
                if in_loop(loop):
                    close_sockets_and_tasks()
                elif not loop.is_closed():
                    loop.call_soon_threadsafe(close_sockets_and_tasks)
            else:
                # Loop has been closed, try to clean up directly.
                del tasks
                del close_sockets_and_tasks
                close_sockets(sockets)
                del self.output_queue_task
                del self.stats_update_task
        else:
            # Sync case.

            # ZMQ context termination can hang if the sockets
            # aren't explicitly closed first.
            close_sockets((self.output_socket, self.input_socket))

            if self.shutdown_path is not None:
                # We must ensure that the sync output socket is
                # closed cleanly in its own thread.
                with self.ctx.socket(zmq.PAIR) as shutdown_sender:
                    shutdown_sender.connect(self.shutdown_path)
                    # Send shutdown signal.
                    shutdown_sender.send(b"")