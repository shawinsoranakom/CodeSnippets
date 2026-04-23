async def test_aexists(self):
        msg = self.not_implemented_msg % "an exists"
        with self.assertRaisesMessage(NotImplementedError, msg):
            await self.session.aexists(None)