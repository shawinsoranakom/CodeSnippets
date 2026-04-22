async def start(self) -> None:
        """Start the runtime. This must be called only once, before
        any other functions are called.

        When this coroutine returns, Streamlit is ready to accept new sessions.

        Notes
        -----
        Threading: UNSAFE. Must be called on the eventloop thread.
        """

        # Create our AsyncObjects. We need to have a running eventloop to
        # instantiate our various synchronization primitives.
        async_objs = AsyncObjects(
            eventloop=asyncio.get_running_loop(),
            must_stop=asyncio.Event(),
            has_connection=asyncio.Event(),
            need_send_data=asyncio.Event(),
            started=asyncio.Future(),
            stopped=asyncio.Future(),
        )
        self._async_objs = async_objs

        if sys.version_info >= (3, 8, 0):
            # Python 3.8+ supports a create_task `name` parameter, which can
            # make debugging a bit easier.
            self._loop_coroutine_task = asyncio.create_task(
                self._loop_coroutine(), name="Runtime.loop_coroutine"
            )
        else:
            self._loop_coroutine_task = asyncio.create_task(self._loop_coroutine())

        await async_objs.started