async def test_acount_does_not_silence_attribute_error_async(self):
        class AttributeErrorContainer:
            async def acount(self):
                raise AttributeError("abc")

        with self.assertRaisesMessage(AttributeError, "abc"):
            await AsyncPaginator(AttributeErrorContainer(), 10).acount()