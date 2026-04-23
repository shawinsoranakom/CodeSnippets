def get_resource_for_path(
    path: str, method: str, path_map: dict[str, dict]
) -> tuple[str | None, dict | None]:
    matches = []
    # creates a regex from the input path if there are parameters, e.g /foo/{bar}/baz -> /foo/[
    # ^\]+/baz, otherwise is a direct match.
    for api_path, details in path_map.items():
        api_path_regex = re.sub(r"{[^+]+\+}", r"[^\?#]+", api_path)
        api_path_regex = re.sub(r"{[^}]+}", r"[^/]+", api_path_regex)
        if re.match(rf"^{api_path_regex}$", path):
            matches.append((api_path, details))

    # if there are no matches, it's not worth to proceed, bail here!
    if not matches:
        LOG.debug("No match found for path: '%s' and method: '%s'", path, method)
        return None, None

    if len(matches) == 1:
        LOG.debug("Match found for path: '%s' and method: '%s'", path, method)
        return matches[0]

    # so we have more than one match
    # /{proxy+} and /api/{proxy+} for inputs like /api/foo/bar
    # /foo/{param1}/baz and /foo/{param1}/{param2} for inputs like /for/bar/baz
    proxy_matches = []
    param_matches = []
    for match in matches:
        match_methods = list(match[1].get("resourceMethods", {}).keys())
        # only look for path matches if the request method is in the resource
        if method.upper() in match_methods or "ANY" in match_methods:
            # check if we have an exact match (exact matches take precedence) if the method is the same
            if match[0] == path:
                return match

            elif path_matches_pattern(path, match[0]):
                # parameters can fit in
                param_matches.append(match)
                continue

            proxy_matches.append(match)

    if param_matches:
        # count the amount of parameters, return the one with the least which is the most precise
        sorted_matches = sorted(param_matches, key=lambda x: x[0].count("{"))
        LOG.debug("Match found for path: '%s' and method: '%s'", path, method)
        return sorted_matches[0]

    if proxy_matches:
        # at this stage, we still have more than one match, but we have an eager example like
        # /{proxy+} or /api/{proxy+}, so we pick the best match by sorting by length, only if they have a method
        # that could match
        sorted_matches = sorted(proxy_matches, key=lambda x: len(x[0]), reverse=True)
        LOG.debug("Match found for path: '%s' and method: '%s'", path, method)
        return sorted_matches[0]

    # if there are no matches with a method that would match, return
    LOG.debug("No match found for method: '%s' for matched path: %s", method, path)
    return None, None