async def test_setdefault_async(self):
        self.assertEqual(await self.session.asetdefault("foo", "bar"), "bar")
        self.assertEqual(await self.session.asetdefault("foo", "baz"), "bar")
        self.assertIs(self.session.accessed, True)
        self.assertIs(self.session.modified, True)