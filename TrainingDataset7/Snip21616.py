def test_update_fk(self):
        obj1, obj2 = CaseTestModel.objects.all()[:2]

        CaseTestModel.objects.update(
            fk=Case(
                When(integer=1, then=obj1.pk),
                When(integer=2, then=obj2.pk),
            ),
        )
        self.assertQuerySetEqual(
            CaseTestModel.objects.order_by("pk"),
            [
                (1, obj1.pk),
                (2, obj2.pk),
                (3, None),
                (2, obj2.pk),
                (3, None),
                (3, None),
                (4, None),
            ],
            transform=attrgetter("integer", "fk_id"),
        )