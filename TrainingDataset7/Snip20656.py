def test_start(self):
        Author.objects.create(name="John Smith", alias="smithj")
        a = Author.objects.annotate(
            name_part_1=Substr("name", 1),
            name_part_2=Substr("name", 2),
        ).get(alias="smithj")

        self.assertEqual(a.name_part_1[1:], a.name_part_2)