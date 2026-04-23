def test_m2m_unmanaged_shadow_models_not_checked(self):
        class A1(models.Model):
            pass

        class C1(models.Model):
            mm_a = models.ManyToManyField(A1, db_table="d1")

        # Unmanaged models that shadow the above models. Reused table names
        # shouldn't be flagged by any checks.
        class A2(models.Model):
            class Meta:
                managed = False

        class C2(models.Model):
            mm_a = models.ManyToManyField(A2, through="Intermediate")

            class Meta:
                managed = False

        class Intermediate(models.Model):
            a2 = models.ForeignKey(A2, models.CASCADE, db_column="a1_id")
            c2 = models.ForeignKey(C2, models.CASCADE, db_column="c1_id")

            class Meta:
                db_table = "d1"
                managed = False

        self.assertEqual(C1.check(), [])
        self.assertEqual(C2.check(), [])