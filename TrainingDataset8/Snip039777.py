async def test_get_async_objs(self):
        """Runtime._get_async_objs() will raise an error if called before the
        Runtime is started, and will return the Runtime's AsyncObjects instance otherwise.
        """
        with self.assertRaises(RuntimeError):
            # Runtime hasn't started yet: error!
            _ = self.runtime._get_async_objs()

        # Runtime has started: no error
        await self.runtime.start()
        self.assertIsInstance(self.runtime._get_async_objs(), AsyncObjects)