def setUpTestData(cls):
        cls.john = Author.objects.create(name="John Smith", alias="smithj")
        cls.elena = Author.objects.create(name="Élena Jordan", alias="elena")
        cls.python = Author.objects.create(name="パイソン")