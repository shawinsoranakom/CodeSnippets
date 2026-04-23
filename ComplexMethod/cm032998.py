def _parse_email_body(
    email_msg: Message,
    email_headers: EmailHeaders,
) -> str:
    body = None
    for part in email_msg.walk():
        if part.is_multipart():
            # Multipart parts are *containers* for other parts, not the actual content itself.
            # Therefore, we skip until we find the individual parts instead.
            continue

        charset = part.get_content_charset() or "utf-8"

        try:
            raw_payload = part.get_payload(decode=True)
            if not isinstance(raw_payload, bytes):
                logging.warning(
                    "Payload section from email was expected to be an array of bytes, instead got "
                    f"{type(raw_payload)=}, {raw_payload=}"
                )
                continue
            body = raw_payload.decode(charset)
            break
        except (UnicodeDecodeError, LookupError) as e:
            logging.warning(f"Could not decode part with charset {charset}. Error: {e}")
            continue

    if not body:
        logging.warning(
            f"Email with {email_headers.id=} has an empty body; returning an empty string"
        )
        return ""

    soup = bs4.BeautifulSoup(markup=body, features="html.parser")

    return " ".join(str_section for str_section in soup.stripped_strings)