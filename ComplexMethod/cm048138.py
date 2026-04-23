def _check_closing_date(self):
        for meeting in self:
            if not meeting.allday and meeting.start and meeting.stop and meeting.stop < meeting.start:
                raise ValidationError(
                    _(
                        "The ending date and time cannot be earlier than the starting date and time.\n"
                        "Meeting “%(name)s” starts at %(start_time)s and ends at %(end_time)s",
                        name=meeting.name,
                        start_time=meeting.start,
                        end_time=meeting.stop,
                    ),
                )
            if meeting.allday and meeting.start_date and meeting.stop_date and meeting.stop_date < meeting.start_date:
                raise ValidationError(
                    _(
                        "The ending date cannot be earlier than the starting date.\n"
                        "Meeting “%(name)s” starts on %(start_date)s and ends on %(end_date)s",
                        name=meeting.name,
                        start_date=meeting.start_date,
                        end_date=meeting.stop_date,
                    ),
                )