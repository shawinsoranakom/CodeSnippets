async def test_custom_expiry_seconds_async(self):
        modification = timezone.now()

        await self.session.aset_expiry(10)

        date = await self.session.aget_expiry_date(modification=modification)
        self.assertEqual(date, modification + timedelta(seconds=10))

        age = await self.session.aget_expiry_age(modification=modification)
        self.assertEqual(age, 10)