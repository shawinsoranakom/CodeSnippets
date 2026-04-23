def get(self, number=5, unread: bool = False):
        """
        Retrieves the last {number} emails from the inbox, optionally filtering for only unread emails.
        """
        if platform.system() != "Darwin":
            return "This method is only supported on MacOS"

        too_many_emails_msg = ""
        if number > 50:
            number = min(number, 50)
            too_many_emails_msg = (
                "This method is limited to 10 emails, returning the first 10: "
            )
        # This is set up to retry if the number of emails is less than the number requested, but only a max of three times
        retries = 0  # Initialize the retry counter
        while retries < 3:
            read_status_filter = "whose read status is false" if unread else ""
            script = f"""
            tell application "{self.mail_app}"
                set latest_messages to messages of inbox {read_status_filter}
                set email_data to {{}}
                repeat with i from 1 to {number}
                    set this_message to item i of latest_messages
                    set end of email_data to {{subject:subject of this_message, sender:sender of this_message, content:content of this_message}}
                end repeat
                return email_data
            end tell
            """
            stdout, stderr = run_applescript_capture(script)

            # if the error is due to not having enough emails, retry with the available emails.
            if "Can’t get item" in stderr:
                match = re.search(r"Can’t get item (\d+) of", stderr)
                if match:
                    available_emails = int(match.group(1)) - 1
                    if available_emails > 0:
                        number = available_emails
                        retries += 1
                        continue
                break
            elif stdout:
                if too_many_emails_msg:
                    return f"{too_many_emails_msg}\n\n{stdout}"
                else:
                    return stdout