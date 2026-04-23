async def test_adelete(self):
        msg = self.not_implemented_msg % "a delete"
        with self.assertRaisesMessage(NotImplementedError, msg):
            await self.session.adelete()