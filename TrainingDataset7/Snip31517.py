def setUp(self):
        # This is executed in autocommit mode so that code in
        # run_select_for_update can see this data.
        self.country1 = Country.objects.create(name="Belgium")
        self.country2 = Country.objects.create(name="France")
        self.city1 = City.objects.create(name="Liberchies", country=self.country1)
        self.city2 = City.objects.create(name="Samois-sur-Seine", country=self.country2)
        self.person = Person.objects.create(
            name="Reinhardt", born=self.city1, died=self.city2
        )
        self.person_profile = PersonProfile.objects.create(person=self.person)

        # We need another database connection in transaction to test that one
        # connection issuing a SELECT ... FOR UPDATE will block.
        self.new_connection = connection.copy()