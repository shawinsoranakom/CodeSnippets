def validate_website_configuration(website_config: WebsiteConfiguration) -> None:
    """
    Validate the website configuration following AWS docs
    See https://docs.aws.amazon.com/AmazonS3/latest/API/API_PutBucketWebsite.html
    :param website_config:
    :raises
    :return: None
    """
    if redirect_all_req := website_config.get("RedirectAllRequestsTo", {}):
        if len(website_config) > 1:
            raise InvalidArgument(
                "RedirectAllRequestsTo cannot be provided in conjunction with other Routing Rules.",
                ArgumentName="RedirectAllRequestsTo",
                ArgumentValue="not null",
            )

        if "HostName" not in redirect_all_req:
            raise MalformedXML()

        if (protocol := redirect_all_req.get("Protocol")) and protocol not in ("http", "https"):
            raise InvalidRequest(
                "Invalid protocol, protocol can be http or https. If not defined the protocol will be selected automatically."
            )

        return

    # required
    # https://docs.aws.amazon.com/AmazonS3/latest/API/API_IndexDocument.html
    if not (index_configuration := website_config.get("IndexDocument")):
        raise InvalidArgument(
            "A value for IndexDocument Suffix must be provided if RedirectAllRequestsTo is empty",
            ArgumentName="IndexDocument",
            ArgumentValue="null",
        )

    if not (index_suffix := index_configuration.get("Suffix")) or "/" in index_suffix:
        raise InvalidArgument(
            "The IndexDocument Suffix is not well formed",
            ArgumentName="IndexDocument",
            ArgumentValue=index_suffix or None,
        )

    if "ErrorDocument" in website_config and not website_config.get("ErrorDocument", {}).get("Key"):
        raise MalformedXML()

    if "RoutingRules" in website_config:
        routing_rules = website_config.get("RoutingRules", [])
        if len(routing_rules) == 0:
            raise MalformedXML()
        if len(routing_rules) > 50:
            raise ValueError("Too many routing rules")  # TODO: correct exception
        for routing_rule in routing_rules:
            redirect = routing_rule.get("Redirect", {})
            # todo: this does not raise an error? check what GetWebsiteConfig returns? empty field?
            # if not (redirect := routing_rule.get("Redirect")):
            #     raise "Something"

            if "ReplaceKeyPrefixWith" in redirect and "ReplaceKeyWith" in redirect:
                raise InvalidRequest(
                    "You can only define ReplaceKeyPrefix or ReplaceKey but not both."
                )

            if "Condition" in routing_rule and not routing_rule.get("Condition", {}):
                raise InvalidRequest(
                    "Condition cannot be empty. To redirect all requests without a condition, the condition element shouldn't be present."
                )

            if (protocol := redirect.get("Protocol")) and protocol not in ("http", "https"):
                raise InvalidRequest(
                    "Invalid protocol, protocol can be http or https. If not defined the protocol will be selected automatically."
                )