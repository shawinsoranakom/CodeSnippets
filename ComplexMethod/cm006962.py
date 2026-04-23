def _get_message_data(self, service: Any, message: Any) -> ChatSession:
                msg = service.users().messages().get(userId="me", id=message["id"]).execute()
                message_content = self._extract_email_content(msg)

                in_reply_to = None
                email_data = msg["payload"]["headers"]
                for values in email_data:
                    name = values["name"]
                    if name == "In-Reply-To":
                        in_reply_to = values["value"]

                thread_id = msg["threadId"]

                if in_reply_to:
                    thread = service.users().threads().get(userId="me", id=thread_id).execute()
                    messages = thread["messages"]

                    response_email = None
                    for _message in messages:
                        email_data = _message["payload"]["headers"]
                        for values in email_data:
                            if values["name"] == "Message-ID":
                                message_id = values["value"]
                                if message_id == in_reply_to:
                                    response_email = _message
                    if response_email is None:
                        msg = "Response email not found in the thread."
                        raise ValueError(msg)
                    starter_content = self._extract_email_content(response_email)
                    return ChatSession(messages=[starter_content, message_content])
                return ChatSession(messages=[message_content])