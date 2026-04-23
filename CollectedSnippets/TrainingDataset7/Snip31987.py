async def test_asave(self):
        msg = self.not_implemented_msg % "a save"
        with self.assertRaisesMessage(NotImplementedError, msg):
            await self.session.asave()