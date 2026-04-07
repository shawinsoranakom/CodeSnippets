def assertDatetimeToTimeKind(kind):
            truncated_start = truncate_to(start_datetime.time(), kind)
            truncated_end = truncate_to(end_datetime.time(), kind)
            queryset = DTModel.objects.annotate(
                truncated=Trunc("start_datetime", kind, output_field=TimeField()),
            ).order_by("start_datetime")
            self.assertSequenceEqual(
                queryset.values_list("start_datetime", "truncated"),
                [
                    (start_datetime, truncated_start),
                    (end_datetime, truncated_end),
                ],
            )