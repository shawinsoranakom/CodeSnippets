async def test_aclear_expired(self):
        self.assertEqual(await self.model.objects.acount(), 0)

        # Object in the future.
        await self.session.aset("key", "value")
        await self.session.aset_expiry(3600)
        await self.session.asave()
        # Object in the past.
        other_session = self.backend()
        await other_session.aset("key", "value")
        await other_session.aset_expiry(-3600)
        await other_session.asave()

        # Two sessions are in the database before clearing expired.
        self.assertEqual(await self.model.objects.acount(), 2)
        await self.session.aclear_expired()
        await other_session.aclear_expired()
        self.assertEqual(await self.model.objects.acount(), 1)