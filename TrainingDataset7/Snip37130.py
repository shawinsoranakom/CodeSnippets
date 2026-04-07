def test_pk_q(self):
        self.assertCountEqual(
            Number.objects.filter(Q(pk=self.numbers[0].pk) ^ Q(pk=self.numbers[1].pk)),
            self.numbers[:2],
        )