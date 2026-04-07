def test_fk_to_smallautofield(self):
        us = Country.objects.create(name="United States")
        City.objects.create(country=us, name="Chicago")
        City.objects.create(country=us, name="New York")

        uk = Country.objects.create(name="United Kingdom", id=2**11)
        City.objects.create(country=uk, name="London")
        City.objects.create(country=uk, name="Edinburgh")