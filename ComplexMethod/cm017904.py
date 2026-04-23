def check_trac_status(ticket_id, ticket_data):
    """The referenced Trac ticket must be Accepted or Ready for checkin,
    unresolved, and assigned.

    ticket_data is the dict returned by fetch_trac_ticket(). Passing None
    skips the check (non-fatal fetch error). Passing TICKET_NOT_FOUND fails
    with a generic not-ready message.
    """
    if ticket_data is None:
        return None  # Non-fatal fetch error; skip.
    if ticket_data is TICKET_NOT_FOUND:
        return Message(
            *INVALID_TRAC_STATUS,
            ticket_id=ticket_id,
            current_state="ticket not found in Trac",
        )
    stage = ticket_data.get("custom", {}).get("stage", "").strip()
    resolution = (ticket_data.get("resolution") or "").strip()
    status = ticket_data.get("status", "").strip()
    if stage in ALLOWED_STAGES and not resolution and status == "assigned":
        return None
    current_state = [
        f"{stage=}" if stage not in ALLOWED_STAGES else "",
        f"{resolution=}" if resolution else "",
        f"{status=}" if status != "assigned" else "",
    ]
    return Message(
        *INVALID_TRAC_STATUS,
        ticket_id=ticket_id,
        current_state=", ".join(s for s in current_state if s),
    )