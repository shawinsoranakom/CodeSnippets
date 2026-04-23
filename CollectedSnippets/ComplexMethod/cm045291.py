async def _run_read_loop(self) -> None:
        logger.info("Starting read loop")
        assert self._host_connection is not None
        # TODO: catch exceptions and reconnect
        while self._running:
            try:
                message = await self._host_connection.recv()
                oneofcase = agent_worker_pb2.Message.WhichOneof(message, "message")
                match oneofcase:
                    case "request":
                        task = asyncio.create_task(self._process_request(message.request))
                        self._background_tasks.add(task)
                        task.add_done_callback(self._raise_on_exception)
                        task.add_done_callback(self._background_tasks.discard)
                    case "response":
                        task = asyncio.create_task(self._process_response(message.response))
                        self._background_tasks.add(task)
                        task.add_done_callback(self._raise_on_exception)
                        task.add_done_callback(self._background_tasks.discard)
                    case "cloudEvent":
                        task = asyncio.create_task(self._process_event(message.cloudEvent))
                        self._background_tasks.add(task)
                        task.add_done_callback(self._raise_on_exception)
                        task.add_done_callback(self._background_tasks.discard)
                    case None:
                        logger.warning("No message")
            except Exception as e:
                logger.error("Error in read loop", exc_info=e)