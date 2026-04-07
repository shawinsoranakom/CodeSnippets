def test_fk_to_bigautofield(self):
        ch = City.objects.create(name="Chicago")
        District.objects.create(city=ch, name="Far South")
        District.objects.create(city=ch, name="North")

        ny = City.objects.create(name="New York", id=2**33)
        District.objects.create(city=ny, name="Brooklyn")
        District.objects.create(city=ny, name="Manhattan")