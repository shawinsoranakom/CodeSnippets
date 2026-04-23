async def _get_thread(
        self, service, thread_id: str, scopes: list[str] | None
    ) -> Thread:
        scopes = [s.lower() for s in (scopes or [])]
        format_type = (
            "metadata"
            if "https://www.googleapis.com/auth/gmail.metadata" in scopes
            else "full"
        )
        thread = await asyncio.to_thread(
            lambda: service.users()
            .threads()
            .get(userId="me", id=thread_id, format=format_type)
            .execute()
        )

        parsed_messages = []
        for msg in thread.get("messages", []):
            headers = {
                h["name"].lower(): h["value"]
                for h in msg.get("payload", {}).get("headers", [])
            }
            body = await self._get_email_body(msg, service)
            attachments = await self._get_attachments(service, msg)

            # Parse all recipients
            to_recipients = [
                addr.strip() for _, addr in getaddresses([headers.get("to", "")])
            ]
            cc_recipients = [
                addr.strip() for _, addr in getaddresses([headers.get("cc", "")])
            ]
            bcc_recipients = [
                addr.strip() for _, addr in getaddresses([headers.get("bcc", "")])
            ]

            email = Email(
                threadId=msg.get("threadId", thread_id),
                labelIds=msg.get("labelIds", []),
                id=msg.get("id"),
                subject=headers.get("subject", "No Subject"),
                snippet=msg.get("snippet", ""),
                from_=parseaddr(headers.get("from", ""))[1],
                to=to_recipients if to_recipients else [],
                cc=cc_recipients,
                bcc=bcc_recipients,
                date=headers.get("date", ""),
                body=body,
                sizeEstimate=msg.get("sizeEstimate", 0),
                attachments=attachments,
            )
            parsed_messages.append(email.model_dump())

        thread["messages"] = parsed_messages
        return thread