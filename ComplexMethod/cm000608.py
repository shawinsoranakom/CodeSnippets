async def run(
        self, input_data: Input, *, credentials: GoogleCredentials, **kwargs
    ) -> BlockOutput:
        try:
            service = self._build_service(credentials, **kwargs)

            # Create event body
            # Get start and end times based on the timing option
            if input_data.timing.discriminator == "exact_timing":
                start_datetime = input_data.timing.start_datetime
                end_datetime = input_data.timing.end_datetime
            else:  # duration_timing
                start_datetime = input_data.timing.start_datetime
                end_datetime = start_datetime + timedelta(
                    minutes=input_data.timing.duration_minutes
                )

            # Format datetimes for Google Calendar API
            start_time_str = start_datetime.isoformat()
            end_time_str = end_datetime.isoformat()

            # Build the event body
            event_body = {
                "summary": input_data.event_title,
                "start": {"dateTime": start_time_str},
                "end": {"dateTime": end_time_str},
            }

            # Add optional fields
            if input_data.location:
                event_body["location"] = input_data.location

            if input_data.description:
                event_body["description"] = input_data.description

            # Add guests
            if input_data.guest_emails:
                event_body["attendees"] = [
                    {"email": email} for email in input_data.guest_emails
                ]

            # Add reminders
            if input_data.reminder_minutes:
                event_body["reminders"] = {
                    "useDefault": False,
                    "overrides": [
                        {"method": "popup", "minutes": reminder.value}
                        for reminder in input_data.reminder_minutes
                    ],
                }

            # Add Google Meet
            if input_data.add_google_meet:
                event_body["conferenceData"] = {
                    "createRequest": {
                        "requestId": f"meet-{uuid.uuid4()}",
                        "conferenceSolutionKey": {"type": "hangoutsMeet"},
                    }
                }

            # Add recurrence
            if input_data.recurrence.discriminator == "recurring":
                rule = f"RRULE:FREQ={input_data.recurrence.frequency.value}"
                rule += f";COUNT={input_data.recurrence.count}"
                event_body["recurrence"] = [rule]

            # Create the event
            result = await asyncio.to_thread(
                self._create_event,
                service=service,
                calendar_id=input_data.calendar_id,
                event_body=event_body,
                send_notifications=input_data.send_notifications,
                conference_data_version=1 if input_data.add_google_meet else 0,
            )

            yield "event_id", result["id"]
            yield "event_link", result["htmlLink"]

        except Exception as e:
            yield "error", str(e)