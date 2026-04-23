def update_firewall_domains(
        self,
        context: RequestContext,
        firewall_domain_list_id: ResourceId,
        operation: FirewallDomainUpdateOperation,
        domains: FirewallDomains,
        **kwargs,
    ) -> UpdateFirewallDomainsResponse:
        """Update the domains in a Firewall Domain List."""
        store = self.get_store(context.account_id, context.region)

        firewall_domain_list: FirewallDomainList = store.get_firewall_domain_list(
            firewall_domain_list_id
        )
        firewall_domains = store.get_firewall_domain(firewall_domain_list_id)

        if operation == FirewallDomainUpdateOperation.ADD:
            if not firewall_domains:
                store.firewall_domains[firewall_domain_list_id] = domains
            else:
                store.firewall_domains[firewall_domain_list_id].append(domains)

        if operation == FirewallDomainUpdateOperation.REMOVE:
            if firewall_domains:
                for domain in domains:
                    if domain in firewall_domains:
                        firewall_domains.remove(domain)
                    else:
                        raise ValidationException(
                            f"[RSLVR-02502] The following domains don't exist in the DNS Firewall domain list '{firewall_domain_list_id}'. You can't delete a domain that isn't in a domain list. Example unknown domain: '{domain}'. Trace Id: '{localstack.services.route53resolver.utils.get_trace_id()}'"
                        )

        if operation == FirewallDomainUpdateOperation.REPLACE:
            store.firewall_domains[firewall_domain_list_id] = domains

        firewall_domain_list["StatusMessage"] = "Finished domain list update"
        firewall_domain_list["ModificationTime"] = datetime.now(UTC).isoformat()
        return UpdateFirewallDomainsResponse(
            Id=firewall_domain_list.get("Id"),
            Name=firewall_domain_list.get("Name"),
            Status=firewall_domain_list.get("Status"),
            StatusMessage=firewall_domain_list.get("StatusMessage"),
        )