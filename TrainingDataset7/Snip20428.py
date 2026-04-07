def assertDateKind(kind):
            truncated_start = truncate_to(start_datetime.date(), kind)
            truncated_end = truncate_to(end_datetime.date(), kind)
            queryset = DTModel.objects.annotate(
                truncated=Trunc("start_date", kind, output_field=DateField())
            ).order_by("start_datetime")
            self.assertSequenceEqual(
                queryset.values_list("start_datetime", "truncated"),
                [
                    (start_datetime, truncated_start),
                    (end_datetime, truncated_end),
                ],
            )