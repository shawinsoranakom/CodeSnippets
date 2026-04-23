def _format_events(self, events: list[dict]) -> list[CalendarEvent]:
        """Format Google Calendar API events into user-friendly structure."""
        formatted_events = []

        for event in events:
            # Determine if all-day event
            is_all_day = "date" in event.get("start", {})

            # Format start and end times
            if is_all_day:
                start_time = event.get("start", {}).get("date", "")
                end_time = event.get("end", {}).get("date", "")
            else:
                # Convert ISO format to more readable format
                start_datetime = datetime.fromisoformat(
                    event.get("start", {}).get("dateTime", "").replace("Z", "+00:00")
                )
                end_datetime = datetime.fromisoformat(
                    event.get("end", {}).get("dateTime", "").replace("Z", "+00:00")
                )
                start_time = start_datetime.strftime("%Y-%m-%d %H:%M")
                end_time = end_datetime.strftime("%Y-%m-%d %H:%M")

            # Extract attendees
            attendees = []
            for attendee in event.get("attendees", []):
                if email := attendee.get("email"):
                    attendees.append(email)

            # Check for video call link
            has_video_call = False
            video_link = None
            if conf_data := event.get("conferenceData"):
                if conf_url := conf_data.get("conferenceUrl"):
                    has_video_call = True
                    video_link = conf_url
                elif entry_points := conf_data.get("entryPoints", []):
                    for entry in entry_points:
                        if entry.get("entryPointType") == "video":
                            has_video_call = True
                            video_link = entry.get("uri")
                            break

            # Create formatted event
            formatted_event = CalendarEvent(
                id=event.get("id", ""),
                title=event.get("summary", "Untitled Event"),
                start_time=start_time,
                end_time=end_time,
                is_all_day=is_all_day,
                location=event.get("location"),
                description=event.get("description"),
                organizer=event.get("organizer", {}).get("email"),
                attendees=attendees,
                has_video_call=has_video_call,
                video_link=video_link,
                calendar_link=event.get("htmlLink", ""),
                is_recurring=bool(event.get("recurrence")),
            )

            formatted_events.append(formatted_event)

        return formatted_events