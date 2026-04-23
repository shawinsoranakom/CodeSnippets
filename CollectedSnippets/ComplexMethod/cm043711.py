async def _resolve_committee_name(
    chamber: str, system_code: str, api_key: str, session=None
) -> str | None:
    """Resolve a committee's libraryOfCongressName from its system code."""
    # pylint: disable=import-outside-toplevel
    from openbb_core.provider.utils.helpers import amake_request

    kwargs: dict = {}
    if session is not None:
        kwargs["session"] = session

    is_sub = len(system_code) > 4 and not system_code.endswith("00")
    lookup_code = system_code[: len(system_code) - 2] + "00" if is_sub else system_code

    url = f"{base_url}committee/{chamber}/{lookup_code}?format=json&api_key={api_key}"
    try:
        resp = await amake_request(url, timeout=15, **kwargs)
    except Exception:
        return None

    if not isinstance(resp, dict):
        return None

    committee = resp.get("committee", {})

    if is_sub:
        for sc in committee.get("subcommittees", []):
            if sc.get("systemCode") == system_code:
                return sc.get("name")

    for h in committee.get("history", []):
        return h.get("libraryOfCongressName") or h.get("officialName", "")

    return committee.get("name")