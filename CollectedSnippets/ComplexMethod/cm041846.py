def delete_event(
        self, event_title: str, start_date: datetime.datetime, calendar: str = None
    ) -> str:
        if platform.system() != "Darwin":
            return "This method is only supported on MacOS"

        # The applescript requires a title and start date to get the right event
        if event_title is None or start_date is None:
            return "Event title and start date are required"

        # If there is no calendar, lets use the first calendar applescript returns. This should probably be modified in the future
        if calendar is None:
            calendar = self.get_first_calendar()
            if not calendar:
                return "Can't find a default calendar. Please try again and specify a calendar name."

        script = f"""
        {makeDateFunction}
        set eventStartDate to makeDate({start_date.strftime("%Y, %m, %d, %H, %M, %S")})
        -- Open and activate calendar first
        tell application "System Events"
            set calendarIsRunning to (name of processes) contains "{self.calendar_app}"
            if calendarIsRunning then
                tell application "{self.calendar_app}" to activate
            else
                tell application "{self.calendar_app}" to launch
                delay 1 -- Wait for the application to open
                tell application "{self.calendar_app}" to activate
            end if
        end tell
        tell application "{self.calendar_app}"
            -- Specify the name of the calendar where the event is located
            set myCalendar to calendar "{calendar}"

            -- Define the exact start date and name of the event to find and delete
            set eventSummary to "{event_title}"

            -- Find the event by start date and summary
            set theEvents to (every event of myCalendar where its start date is eventStartDate and its summary is eventSummary)

            -- Check if any events were found
            if (count of theEvents) is equal to 0 then
                return "No matching event found to delete."
            else
                -- If the event is found, delete it
                repeat with theEvent in theEvents
                    delete theEvent
                end repeat
                save
                return "Event deleted successfully."
            end if
        end tell
        """

        stderr, stdout = run_applescript_capture(script)
        if stdout:
            return stdout[0].strip()
        elif stderr:
            if "successfully" in stderr:
                return stderr

            return f"""Error deleting event: {stderr}"""
        else:
            return "Unknown error deleting event. Please check event title and date."