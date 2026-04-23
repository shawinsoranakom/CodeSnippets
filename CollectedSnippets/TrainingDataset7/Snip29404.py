async def test_acount_does_not_silence_type_error_async(self):
        class TypeErrorContainer:
            async def acount(self):
                raise TypeError("abc")

        with self.assertRaisesMessage(TypeError, "abc"):
            await AsyncPaginator(TypeErrorContainer(), 10).acount()