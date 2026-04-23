def test_one_to_one_relation(self):
        qs = Reference.objects.order_by("proof")
        self.assertIs(qs.totally_ordered, False)
        qs = Reference.objects.order_by("proof_id")
        self.assertIs(qs.totally_ordered, True)