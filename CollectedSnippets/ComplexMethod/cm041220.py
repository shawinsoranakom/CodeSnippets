def get_available_dns_server():
    #  TODO check if more loop-checks are necessary than just not using our own DNS server
    with FALLBACK_DNS_LOCK:
        resolver = dns.resolver.Resolver()
        # we do not want to include localhost here, or a loop might happen
        candidates = [r for r in resolver.nameservers if r != "127.0.0.1"]
        result = None
        candidates.append(DEFAULT_FALLBACK_DNS_SERVER)
        for ns in candidates:
            resolver.nameservers = [ns]
            try:
                try:
                    answer = resolver.resolve(VERIFICATION_DOMAIN, "a", lifetime=3)
                    answer = [
                        res.to_text() for answers in answer.response.answer for res in answers.items
                    ]
                except Timeout:
                    answer = None
                if not answer:
                    continue
                result = ns
                break
            except Exception:
                pass

        if result:
            LOG.debug("Determined fallback dns: %s", result)
        else:
            LOG.info(
                "Unable to determine fallback DNS. Please check if '%s' is reachable by your configured DNS servers"
                "DNS fallback will be disabled.",
                VERIFICATION_DOMAIN,
            )
        return result