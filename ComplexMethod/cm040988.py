def update_firewall_rule(
        self,
        context: RequestContext,
        firewall_rule_group_id: ResourceId,
        firewall_domain_list_id: ResourceId = None,
        firewall_threat_protection_id: ResourceId = None,
        priority: Priority = None,
        action: Action = None,
        block_response: BlockResponse = None,
        block_override_domain: BlockOverrideDomain = None,
        block_override_dns_type: BlockOverrideDnsType = None,
        block_override_ttl: BlockOverrideTtl = None,
        name: Name = None,
        firewall_domain_redirection_action: FirewallDomainRedirectionAction = None,
        qtype: Qtype = None,
        dns_threat_protection: DnsThreatProtection = None,
        confidence_threshold: ConfidenceThreshold = None,
        **kwargs,
    ) -> UpdateFirewallRuleResponse:
        """Updates a firewall rule"""
        store = self.get_store(context.account_id, context.region)
        firewall_rule: FirewallRule = store.get_firewall_rule(
            firewall_rule_group_id, firewall_domain_list_id
        )

        if priority:
            firewall_rule["Priority"] = priority
        if action:
            firewall_rule["Action"] = action
        if block_response:
            firewall_rule["BlockResponse"] = block_response
        if block_override_domain:
            firewall_rule["BlockOverrideDomain"] = block_override_domain
        if block_override_dns_type:
            firewall_rule["BlockOverrideDnsType"] = block_override_dns_type
        if block_override_ttl:
            firewall_rule["BlockOverrideTtl"] = block_override_ttl
        if name:
            firewall_rule["Name"] = name
        if firewall_domain_redirection_action:
            firewall_rule["FirewallDomainRedirectionAction"] = firewall_domain_redirection_action
        if qtype:
            firewall_rule["Qtype"] = qtype
        return UpdateFirewallRuleResponse(
            FirewallRule=firewall_rule,
        )