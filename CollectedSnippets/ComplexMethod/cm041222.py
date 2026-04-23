def _resolve_alias(
        self, request: DNSRecord, reply: DNSRecord, client_address: ClientAddress
    ) -> bool:
        if request.q.qtype in (QTYPE.A, QTYPE.AAAA, QTYPE.CNAME):
            if aliases := self._find_matching_aliases(request.q):
                for alias in aliases:
                    # if there is no health check, or the healthcheck is successful, we will consider this alias
                    # take the first alias passing this check
                    if not alias.health_check or alias.health_check():
                        request_copy: DNSRecord = copy.deepcopy(request)
                        request_copy.q.qname = alias.target
                        # check if we can resolve the alias
                        found = self._resolve_name_from_zones(request_copy, reply, client_address)
                        if found:
                            LOG.debug(
                                "Found entry for AliasTarget '%s' ('%s')", request.q.qname, alias
                            )
                            # change the replaced rr-DNS names back to the original request
                            for rr in reply.rr:
                                rr.set_rname(request.q.qname)
                        else:
                            reply.header.set_rcode(RCODE.REFUSED)
                        return True
        return False