def create_ponies(models, schema_editor):
            Pony = models.get_model("test_runpython", "Pony")
            pony1 = Pony.objects.create(pink=1, weight=3.55)
            self.assertIsNot(pony1.pk, None)
            pony2 = Pony.objects.create(weight=5)
            self.assertIsNot(pony2.pk, None)
            self.assertNotEqual(pony1.pk, pony2.pk)