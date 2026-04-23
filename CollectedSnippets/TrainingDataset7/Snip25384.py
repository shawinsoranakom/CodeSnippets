def test_m2m_to_concrete_and_proxy_allowed(self):
        class A(models.Model):
            pass

        class Through(models.Model):
            a = models.ForeignKey("A", models.CASCADE)
            c = models.ForeignKey("C", models.CASCADE)

        class ThroughProxy(Through):
            class Meta:
                proxy = True

        class C(models.Model):
            mm_a = models.ManyToManyField(A, through=Through)
            mm_aproxy = models.ManyToManyField(
                A, through=ThroughProxy, related_name="proxied_m2m"
            )

        self.assertEqual(C.check(), [])