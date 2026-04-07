def repercent_broken_unicode(path):
    """
    As per RFC 3987 Section 3.2, step three of converting a URI into an IRI,
    repercent-encode any octet produced that is not part of a strictly legal
    UTF-8 octet sequence.
    """
    changed_parts = []
    while True:
        try:
            path.decode()
        except UnicodeDecodeError as e:
            # CVE-2019-14235: A recursion shouldn't be used since the exception
            # handling uses massive amounts of memory
            repercent = quote(path[e.start : e.end], safe=b"/#%[]=:;$&()+,!?*@'~")
            changed_parts.append(path[: e.start] + repercent.encode())
            path = path[e.end :]
        else:
            return b"".join(changed_parts) + path