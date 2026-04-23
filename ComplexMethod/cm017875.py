def handle_word(
        self,
        word,
        *,
        safe_input,
        trim_url_limit=None,
        nofollow=False,
        autoescape=False,
    ):
        if "." in word or "@" in word or ":" in word:
            # lead: Punctuation trimmed from the beginning of the word.
            # middle: State of the word.
            # trail: Punctuation trimmed from the end of the word.
            lead, middle, trail = self.trim_punctuation(word)
            # Make URL we want to point to.
            url = None
            nofollow_attr = ' rel="nofollow"' if nofollow else ""
            if len(middle) <= MAX_URL_LENGTH and self.simple_url_re.match(middle):
                url = smart_urlquote(html.unescape(middle))
            elif len(middle) <= MAX_URL_LENGTH and self.simple_url_2_re.match(middle):
                unescaped_middle = html.unescape(middle)
                # RemovedInDjango70Warning: When the deprecation ends, replace
                # with:
                # url = smart_urlquote(f"https://{unescaped_middle}")
                protocol = (
                    "https"
                    if getattr(settings, "URLIZE_ASSUME_HTTPS", False)
                    else "http"
                )
                if not settings.URLIZE_ASSUME_HTTPS:
                    warnings.warn(
                        "The default protocol will be changed from HTTP to "
                        "HTTPS in Django 7.0. Set the URLIZE_ASSUME_HTTPS "
                        "transitional setting to True to opt into using HTTPS as the "
                        "new default protocol.",
                        RemovedInDjango70Warning,
                        stacklevel=2,
                    )
                url = smart_urlquote(f"{protocol}://{unescaped_middle}")
            elif ":" not in middle and self.is_email_simple(middle):
                local, domain = middle.rsplit("@", 1)
                # Encode per RFC 6068 Section 2 (items 1, 4, 5). Defer any IDNA
                # to the user agent. See #36013.
                local = quote(local, safe="")
                domain = quote(domain, safe="")
                url = self.mailto_template.format(local=local, domain=domain)
                nofollow_attr = ""
            # Make link.
            if url:
                trimmed = self.trim_url(middle, limit=trim_url_limit)
                if autoescape and not safe_input:
                    lead, trail = escape(lead), escape(trail)
                    trimmed = escape(trimmed)
                middle = self.url_template.format(
                    href=escape(url),
                    attrs=nofollow_attr,
                    url=trimmed,
                )
                return SafeString(f"{lead}{middle}{trail}")
            else:
                if safe_input:
                    return mark_safe(word)
                elif autoescape:
                    return escape(word)
        elif safe_input:
            return mark_safe(word)
        elif autoescape:
            return escape(word)
        return word