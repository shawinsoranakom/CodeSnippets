def create_shetlandponies(models, schema_editor):
            ShetlandPony = models.get_model("test_runpython", "ShetlandPony")
            pony1 = ShetlandPony.objects.create(weight=4.0)
            self.assertIsNot(pony1.pk, None)
            pony2 = ShetlandPony.objects.create(weight=5.0)
            self.assertIsNot(pony2.pk, None)
            self.assertNotEqual(pony1.pk, pony2.pk)