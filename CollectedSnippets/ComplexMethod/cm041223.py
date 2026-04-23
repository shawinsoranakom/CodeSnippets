def _resolve_name_from_zones(
        self, request: DNSRecord, reply: DNSRecord, client_address: ClientAddress
    ) -> bool:
        found = False

        converter = RecordConverter(request, client_address)

        # check for direct (not regex based) response
        zone = self.zones.get(normalise_dns_name(request.q.qname))
        if zone is not None:
            for zone_records in zone:
                rr = converter.to_record(zone_records).try_rr(request.q)
                if rr:
                    found = True
                    reply.add_answer(rr)
        else:
            # no direct zone so look for an SOA record for a higher level zone
            for zone_label, zone_records in self.zones.items():
                # try regex match
                pattern = re.sub(r"(^|[^.])\*", ".*", str(zone_label))
                if re.match(pattern, str(request.q.qname)):
                    for record in zone_records:
                        rr = converter.to_record(record).try_rr(request.q)
                        if rr:
                            found = True
                            reply.add_answer(rr)
                # try suffix match
                elif request.q.qname.matchSuffix(to_bytes(zone_label)):
                    try:
                        soa_record = next(r for r in zone_records if converter.to_record(r).is_soa)
                    except StopIteration:
                        continue
                    else:
                        found = True
                        reply.add_answer(converter.to_record(soa_record).as_rr(zone_label))
                        break
        return found