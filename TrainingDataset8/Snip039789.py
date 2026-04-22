async def asyncTearDown(self):
        # Stop the runtime, and return when it's stopped
        if self.runtime.state != RuntimeState.INITIAL:
            self.runtime.stop()
            await self.runtime.stopped
        Runtime._instance = None