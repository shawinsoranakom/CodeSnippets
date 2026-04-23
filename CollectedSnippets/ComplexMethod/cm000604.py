async def _read_emails(
        self,
        service,
        query: str | None,
        max_results: int | None,
        scopes: list[str] | None,
    ) -> list[Email]:
        scopes = [s.lower() for s in (scopes or [])]
        list_kwargs = {"userId": "me", "maxResults": max_results or 10}
        if query and "https://www.googleapis.com/auth/gmail.metadata" not in scopes:
            list_kwargs["q"] = query

        results = await asyncio.to_thread(
            lambda: service.users().messages().list(**list_kwargs).execute()
        )

        messages = results.get("messages", [])

        email_data = []
        for message in messages:
            format_type = (
                "metadata"
                if "https://www.googleapis.com/auth/gmail.metadata" in scopes
                else "full"
            )
            msg = await asyncio.to_thread(
                lambda: service.users()
                .messages()
                .get(userId="me", id=message["id"], format=format_type)
                .execute()
            )

            headers = {
                header["name"].lower(): header["value"]
                for header in msg["payload"]["headers"]
            }

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
                threadId=msg.get("threadId", None),
                labelIds=msg.get("labelIds", []),
                id=msg["id"],
                subject=headers.get("subject", "No Subject"),
                snippet=msg.get("snippet", ""),
                from_=parseaddr(headers.get("from", ""))[1],
                to=to_recipients if to_recipients else [],
                cc=cc_recipients,
                bcc=bcc_recipients,
                date=headers.get("date", ""),
                body=await self._get_email_body(msg, service),
                sizeEstimate=msg.get("sizeEstimate", 0),
                attachments=attachments,
            )
            email_data.append(email)

        return email_data