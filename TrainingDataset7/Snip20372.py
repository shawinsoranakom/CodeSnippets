def create_model(self, start_datetime, end_datetime):
        return DTModel.objects.create(
            name=start_datetime.isoformat() if start_datetime else "None",
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            start_date=start_datetime.date() if start_datetime else None,
            end_date=end_datetime.date() if end_datetime else None,
            start_time=start_datetime.time() if start_datetime else None,
            end_time=end_datetime.time() if end_datetime else None,
            duration=(
                (end_datetime - start_datetime)
                if start_datetime and end_datetime
                else None
            ),
        )