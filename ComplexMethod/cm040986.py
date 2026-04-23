def Route53ResolverBackend_matched_arn(fn, self, resource_arn):
    """Given ARN, raise exception if there is no corresponding resource."""
    account_id = extract_account_id_from_arn(resource_arn)
    region_name = extract_region_from_arn(resource_arn)
    store = Route53ResolverProvider.get_store(account_id, region_name)

    for firewall_rule_group in store.firewall_rule_groups.values():
        if firewall_rule_group.get("Arn") == resource_arn:
            return
    for firewall_domain_list in store.firewall_domain_lists.values():
        if firewall_domain_list.get("Arn") == resource_arn:
            return
    for firewall_rule_group_association in store.firewall_rule_group_associations.values():
        if firewall_rule_group_association.get("Arn") == resource_arn:
            return
    for resolver_query_log_config in store.resolver_query_log_configs.values():
        if resolver_query_log_config.get("Arn") == resource_arn:
            return
    fn(self, resource_arn)