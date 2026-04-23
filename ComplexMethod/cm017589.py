def get_change_message(self):
        """
        If self.change_message is a JSON structure, interpret it as a change
        string, properly translated.
        """
        if self.change_message and self.change_message[0] == "[":
            try:
                change_message = json.loads(self.change_message)
            except json.JSONDecodeError:
                return self.change_message
            messages = []
            for sub_message in change_message:
                if "added" in sub_message:
                    if sub_message["added"]:
                        sub_message["added"]["name"] = gettext(
                            sub_message["added"]["name"]
                        )
                        messages.append(
                            gettext("Added {name} “{object}”.").format(
                                **sub_message["added"]
                            )
                        )
                    else:
                        messages.append(gettext("Added."))

                elif "changed" in sub_message:
                    sub_message["changed"]["fields"] = get_text_list(
                        [
                            gettext(field_name)
                            for field_name in sub_message["changed"]["fields"]
                        ],
                        gettext("and"),
                    )
                    if "name" in sub_message["changed"]:
                        sub_message["changed"]["name"] = gettext(
                            sub_message["changed"]["name"]
                        )
                        messages.append(
                            gettext("Changed {fields} for {name} “{object}”.").format(
                                **sub_message["changed"]
                            )
                        )
                    else:
                        messages.append(
                            gettext("Changed {fields}.").format(
                                **sub_message["changed"]
                            )
                        )

                elif "deleted" in sub_message:
                    sub_message["deleted"]["name"] = gettext(
                        sub_message["deleted"]["name"]
                    )
                    messages.append(
                        gettext("Deleted {name} “{object}”.").format(
                            **sub_message["deleted"]
                        )
                    )

            change_message = " ".join(msg[0].upper() + msg[1:] for msg in messages)
            return change_message or gettext("No fields changed.")
        else:
            return self.change_message