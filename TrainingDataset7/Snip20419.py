def test_extract_outerref(self):
        datetime_1 = datetime.datetime(2000, 1, 1)
        datetime_2 = datetime.datetime(2001, 3, 5)
        datetime_3 = datetime.datetime(2002, 1, 3)
        if settings.USE_TZ:
            datetime_1 = timezone.make_aware(datetime_1)
            datetime_2 = timezone.make_aware(datetime_2)
            datetime_3 = timezone.make_aware(datetime_3)
        obj_1 = self.create_model(datetime_1, datetime_3)
        obj_2 = self.create_model(datetime_2, datetime_1)
        obj_3 = self.create_model(datetime_3, datetime_2)

        inner_qs = DTModel.objects.filter(
            start_datetime__year=2000,
            start_datetime__month=ExtractMonth(OuterRef("end_datetime")),
        )
        qs = DTModel.objects.annotate(
            related_pk=Subquery(inner_qs.values("pk")[:1]),
        )
        self.assertSequenceEqual(
            qs.order_by("name").values("pk", "related_pk"),
            [
                {"pk": obj_1.pk, "related_pk": obj_1.pk},
                {"pk": obj_2.pk, "related_pk": obj_1.pk},
                {"pk": obj_3.pk, "related_pk": None},
            ],
        )