def setUpTestData(cls):
        cls.s1 = Season.objects.create(year=1942, gt=1942)
        cls.s2 = Season.objects.create(year=1842, gt=1942, nulled_text_field="text")
        cls.s3 = Season.objects.create(year=2042, gt=1942)
        Game.objects.create(season=cls.s1, home="NY", away="Boston")
        Game.objects.create(season=cls.s1, home="NY", away="Tampa")
        Game.objects.create(season=cls.s3, home="Boston", away="Tampa")