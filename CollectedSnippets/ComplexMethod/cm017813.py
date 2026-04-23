def prep_address(self, address, force_ascii=True):
        """
        Return the addr-spec portion of an email address. Raises ValueError for
        invalid addresses, including CR/NL injection.

        If force_ascii is True, apply IDNA encoding to non-ASCII domains, and
        raise ValueError for non-ASCII local-parts (which can't be encoded).
        Otherwise, leave Unicode characters unencoded (e.g., for sending with
        SMTPUTF8).
        """
        address = force_str(address)
        parsed = AddressHeader.value_parser(address)
        defects = set(str(defect) for defect in parsed.all_defects)
        # Django allows local mailboxes like "From: webmaster" (#15042).
        defects.discard("addr-spec local part with no domain")
        if not force_ascii:
            # Non-ASCII local-part is valid with SMTPUTF8. Remove once
            # https://github.com/python/cpython/issues/81074 is fixed.
            defects.discard("local-part contains non-ASCII characters)")
        if defects:
            raise ValueError(f"Invalid address {address!r}: {'; '.join(defects)}")

        mailboxes = parsed.all_mailboxes
        if len(mailboxes) != 1:
            raise ValueError(f"Invalid address {address!r}: must be a single address")

        mailbox = mailboxes[0]
        if force_ascii and mailbox.domain and not mailbox.domain.isascii():
            # Re-compose an addr-spec with the IDNA encoded domain.
            domain = punycode(mailbox.domain)
            return str(Address(username=mailbox.local_part, domain=domain))
        else:
            return mailbox.addr_spec