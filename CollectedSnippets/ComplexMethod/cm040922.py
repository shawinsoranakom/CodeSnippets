def _transform_website_configuration(self, website_configuration: dict) -> dict:
        if not website_configuration:
            return {}
        output = {}
        if index := website_configuration.get("IndexDocument"):
            output["IndexDocument"] = {"Suffix": index}
        if error := website_configuration.get("ErrorDocument"):
            output["ErrorDocument"] = {"Key": error}
        if redirect_all := website_configuration.get("RedirectAllRequestsTo"):
            output["RedirectAllRequestsTo"] = redirect_all

        for r in website_configuration.get("RoutingRules", []):
            rule = {}
            if condition := r.get("RoutingRuleCondition"):
                rule["Condition"] = condition
            if redirect := r.get("RedirectRule"):
                rule["Redirect"] = redirect
            output.setdefault("RoutingRules", []).append(rule)

        return output