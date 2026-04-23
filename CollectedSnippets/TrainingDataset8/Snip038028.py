async def _loop_coroutine(self) -> None:
        """The main Runtime loop.

        This function won't exit until `stop` is called.

        Notes
        -----
        Threading: UNSAFE. Must be called on the eventloop thread.
        """

        async_objs = self._get_async_objs()

        try:
            if self._state == RuntimeState.INITIAL:
                self._set_state(RuntimeState.NO_SESSIONS_CONNECTED)
            elif self._state == RuntimeState.ONE_OR_MORE_SESSIONS_CONNECTED:
                pass
            else:
                raise RuntimeError(f"Bad Runtime state at start: {self._state}")

            # Signal that we're started and ready to accept sessions
            async_objs.started.set_result(None)

            while not async_objs.must_stop.is_set():
                if self._state == RuntimeState.NO_SESSIONS_CONNECTED:
                    await asyncio.wait(
                        (
                            asyncio.create_task(async_objs.must_stop.wait()),
                            asyncio.create_task(async_objs.has_connection.wait()),
                        ),
                        return_when=asyncio.FIRST_COMPLETED,
                    )

                elif self._state == RuntimeState.ONE_OR_MORE_SESSIONS_CONNECTED:
                    async_objs.need_send_data.clear()

                    # Shallow-clone our sessions into a list, so we can iterate
                    # over it and not worry about whether it's being changed
                    # outside this coroutine.
                    session_infos = list(self._session_info_by_id.values())

                    for session_info in session_infos:
                        msg_list = session_info.session.flush_browser_queue()
                        for msg in msg_list:
                            try:
                                self._send_message(session_info, msg)
                            except SessionClientDisconnectedError:
                                self.close_session(session_info.session.id)

                            # Yield for a tick after sending a message.
                            await asyncio.sleep(0)

                    # Yield for a few milliseconds between session message
                    # flushing.
                    await asyncio.sleep(0.01)

                else:
                    # Break out of the thread loop if we encounter any other state.
                    break

                await asyncio.wait(
                    (
                        asyncio.create_task(async_objs.must_stop.wait()),
                        asyncio.create_task(async_objs.need_send_data.wait()),
                    ),
                    return_when=asyncio.FIRST_COMPLETED,
                )

            # Shut down all AppSessions
            for session_info in list(self._session_info_by_id.values()):
                session_info.session.shutdown()

            self._set_state(RuntimeState.STOPPED)
            async_objs.stopped.set_result(None)

        except Exception as e:
            async_objs.stopped.set_exception(e)
            traceback.print_exc()
            LOGGER.info(
                """
Please report this bug at https://github.com/streamlit/streamlit/issues.
"""
            )