def email_split_tuples(text):
    """ Return a list of (name, email) address tuples found in ``text`` . Note
    that text should be an email header or a stringified email list as it may
    give broader results than expected on actual text. """
    def _parse_based_on_spaces(pair):
        """ With input 'name email@domain.com' (missing quotes for a formatting)
        getaddresses returns ('', 'name email@domain.com). This when having no
        name and an email a fallback to enhance parsing is to redo a getaddresses
        by replacing spaces by commas. The new email will be split into sub pairs
        allowing to find the email and name parts, allowing to make a new name /
        email pair. Emails should not contain spaces thus this is coherent with
        email formation. """
        name, email = pair
        if not name and email and ' ' in email:
            inside_pairs = getaddresses([email.replace(' ', ',')])
            name_parts, found_email = [], False
            for pair in inside_pairs:
                if pair[1] and '@' not in pair[1]:
                    name_parts.append(pair[1])
                if pair[1] and '@' in pair[1]:
                    found_email = pair[1]
            name, email = (' '.join(name_parts), found_email) if found_email else (name, email)
        return (name, email)

    if not text:
        return []

    # found valid pairs, filtering out failed parsing
    valid_pairs = [
        (addr[0], addr[1]) for addr in getaddresses([text])
        # getaddresses() returns '' when email parsing fails, and
        # sometimes returns emails without at least '@'. The '@'
        # is strictly required in RFC2822's `addr-spec`.
        if addr[1] and '@' in addr[1]
    ]
    # corner case: returning '@gmail.com'-like email (see test_email_split)
    if any(pair[1].startswith('@') for pair in valid_pairs):
        filtered = [
            found_email for found_email in email_re.findall(text)
            if found_email and not found_email.startswith('@')
        ]
        if filtered:
            valid_pairs = [('', found_email) for found_email in filtered]

    return list(map(_parse_based_on_spaces, valid_pairs))