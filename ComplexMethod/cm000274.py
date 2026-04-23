def emails_from_url(url: str = "https://github.com") -> list[str]:
    """
    This function takes url and return all valid urls
    """
    # Get the base domain from the url
    domain = get_domain_name(url)

    # Initialize the parser
    parser = Parser(domain)

    try:
        # Open URL
        r = httpx.get(url, timeout=10, follow_redirects=True)

        # pass the raw HTML to the parser to get links
        parser.feed(r.text)

        # Get links and loop through
        valid_emails = set()
        for link in parser.urls:
            # open URL.
            # Check if the link is already absolute
            if not link.startswith("http://") and not link.startswith("https://"):
                # Prepend protocol only if link starts with domain, normalize otherwise
                if link.startswith(domain):
                    link = f"https://{link}"
                else:
                    link = parse.urljoin(f"https://{domain}", link)
            try:
                read = httpx.get(link, timeout=10, follow_redirects=True)
                # Get the valid email.
                emails = re.findall("[a-zA-Z0-9]+@" + domain, read.text)
                # If not in list then append it.
                for email in emails:
                    valid_emails.add(email)
            except ValueError:
                pass
    except ValueError:
        raise SystemExit(1)

    # Finally return a sorted list of email addresses with no duplicates.
    return sorted(valid_emails)