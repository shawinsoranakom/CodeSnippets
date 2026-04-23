async def asyncSetUp(self):
        # We don't call super().asyncSetUp() here. (Our superclass creates
        # its own Runtime instance with a mock script_path, but we want
        # to specify a non-mocked path.)
        config = RuntimeConfig(
            script_path=self._path,
            command_line="mock command line",
            media_file_storage=MemoryMediaFileStorage("/mock/media"),
        )
        self.runtime = Runtime(config)
        await self.runtime.start()