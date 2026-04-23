def setUp(self):
        super().setUp()
        self.blues = Band.objects.create(name="Bogey Blues")
        self.potatoes = Band.objects.create(name="Green Potatoes")