def _match_rule(rule: CORSRule, method: str, headers: Headers) -> CORSRule | None:
        """
        Check if the request method and headers matches the given CORS rule.
        :param rule: CORSRule: a CORS Rule from the bucket
        :param method: HTTP method of the request
        :param headers: Headers of the request
        :return: CORSRule if the rule match, or None
        """
        # AWS treats any method as an OPTIONS if it has the specific OPTIONS CORS headers
        request_method = headers.get("Access-Control-Request-Method") or method
        origin = headers.get("Origin")
        if request_method not in rule["AllowedMethods"]:
            return

        if "*" not in rule["AllowedOrigins"] and not any(
            # Escapes any characters that needs escaping and replaces * with .+
            # Transforms http://*.localhost:1234 to http://.+\\.localhost:1234
            re.match(re.escape(allowed_origin).replace("\\*", ".+") + "$", origin)
            for allowed_origin in rule["AllowedOrigins"]
        ):
            return

        if request_headers := headers.get("Access-Control-Request-Headers"):
            if not (allowed_headers := rule.get("AllowedHeaders")):
                return

            lower_case_allowed_headers = {header.lower() for header in allowed_headers}
            if "*" not in allowed_headers and not all(
                header.strip() in lower_case_allowed_headers
                for header in request_headers.lower().split(",")
            ):
                return

        return rule