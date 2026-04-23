def test_ticket7277(self):
        self.assertSequenceEqual(
            self.n1.annotation_set.filter(
                Q(tag=self.t5)
                | Q(tag__children=self.t5)
                | Q(tag__children__children=self.t5)
            ),
            [self.ann1],
        )