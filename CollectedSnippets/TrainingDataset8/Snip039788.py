async def asyncSetUp(self):
        config = RuntimeConfig(
            script_path="mock/script/path.py",
            command_line="",
            media_file_storage=MemoryMediaFileStorage("/mock/media"),
        )
        self.runtime = Runtime(config)