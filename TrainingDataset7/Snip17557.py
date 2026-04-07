async def test_araises_exception(self):
        msg = (
            "No authentication backends have been defined. "
            "Does AUTHENTICATION_BACKENDS contain anything?"
        )
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            await self.user.ahas_perm(("perm", TestObj()))