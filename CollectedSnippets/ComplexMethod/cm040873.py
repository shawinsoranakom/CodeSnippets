def _find_matching_rule(
        routing_rules: RoutingRules, object_key: ObjectKey, error_code: int = None
    ) -> RoutingRule | None:
        """
        Iterate over the routing rules set in the configuration, and return the first that match the key name and/or the
        error code (in the 4XX range).
        :param routing_rules: RoutingRules part of WebsiteConfiguration
        :param object_key: ObjectKey
        :param error_code: error code of the Response in the 4XX range
        :return: a RoutingRule if matched, or None
        """
        # TODO: we could separate rules depending in they have the HttpErrorCodeReturnedEquals field
        #  we would not try to match on them early, no need to iterate on them
        #  and iterate them over only if an exception is encountered
        for rule in routing_rules:
            if condition := rule.get("Condition"):
                prefix = condition.get("KeyPrefixEquals")
                return_http_code = condition.get("HttpErrorCodeReturnedEquals")
                # if both prefix matching and http error matching conditions are set
                if prefix and return_http_code:
                    if object_key.startswith(prefix) and error_code == int(return_http_code):
                        return rule
                    else:
                        # it must either match both or it does not apply
                        continue
                # only prefix is set, but this should have been matched before the error
                elif prefix and object_key.startswith(prefix):
                    return rule
                elif return_http_code and error_code == int(return_http_code):
                    return rule

            else:
                # if no Condition is set, the redirect is applied to all requests
                return rule