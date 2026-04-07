async def test_aexists(self):
        check = await SimpleModel.objects.filter(field=1).aexists()
        self.assertIs(check, True)

        check = await SimpleModel.objects.filter(field=4).aexists()
        self.assertIs(check, False)