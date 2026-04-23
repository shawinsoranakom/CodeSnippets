def get_obs_route(value):
    """ obs-route = obs-domain-list ":"
        obs-domain-list = *(CFWS / ",") "@" domain *("," [CFWS] ["@" domain])

        Returns an obs-route token with the appropriate sub-tokens (that is,
        there is no obs-domain-list in the parse tree).
    """
    obs_route = ObsRoute()
    while value and (value[0]==',' or value[0] in CFWS_LEADER):
        if value[0] in CFWS_LEADER:
            token, value = get_cfws(value)
            obs_route.append(token)
        elif value[0] == ',':
            obs_route.append(ListSeparator)
            value = value[1:]
    if not value or value[0] != '@':
        raise errors.HeaderParseError(
            "expected obs-route domain but found '{}'".format(value))
    obs_route.append(RouteComponentMarker)
    token, value = get_domain(value[1:])
    obs_route.append(token)
    while value and value[0]==',':
        obs_route.append(ListSeparator)
        value = value[1:]
        if not value:
            break
        if value[0] in CFWS_LEADER:
            token, value = get_cfws(value)
            obs_route.append(token)
        if not value:
            break
        if value[0] == '@':
            obs_route.append(RouteComponentMarker)
            token, value = get_domain(value[1:])
            obs_route.append(token)
    if not value:
        raise errors.HeaderParseError("end of header while parsing obs-route")
    if value[0] != ':':
        raise errors.HeaderParseError( "expected ':' marking end of "
            "obs-route but found '{}'".format(value))
    obs_route.append(ValueTerminal(':', 'end-of-obs-route-marker'))
    return obs_route, value[1:]