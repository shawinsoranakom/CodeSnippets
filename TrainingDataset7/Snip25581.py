def test_no_clash_for_hidden_related_name(self):
        class Stub(models.Model):
            pass

        class ManyToManyRel(models.Model):
            thing1 = models.ManyToManyField(Stub, related_name="+")
            thing2 = models.ManyToManyField(Stub, related_name="+")

        class FKRel(models.Model):
            thing1 = models.ForeignKey(Stub, models.CASCADE, related_name="+")
            thing2 = models.ForeignKey(Stub, models.CASCADE, related_name="+")

        self.assertEqual(ManyToManyRel.check(), [])
        self.assertEqual(FKRel.check(), [])