def setUpClass(cls):
        super().setUpClass()
        cls.elvis = Person.objects.get(name="Elvis Presley")