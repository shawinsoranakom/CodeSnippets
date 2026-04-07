async def test_aload(self):
        msg = self.not_implemented_msg % "a load"
        with self.assertRaisesMessage(NotImplementedError, msg):
            await self.session.aload()