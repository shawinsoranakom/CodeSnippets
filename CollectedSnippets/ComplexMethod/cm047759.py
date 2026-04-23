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