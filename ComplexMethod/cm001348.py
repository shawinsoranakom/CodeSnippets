def apply_overrides_to_ai_settings(
    ai_profile: AIProfile,
    directives: AIDirectives,
    override_name: Optional[str] = "",
    override_role: Optional[str] = "",
    replace_directives: bool = False,
    resources: Optional[list[str]] = None,
    constraints: Optional[list[str]] = None,
    best_practices: Optional[list[str]] = None,
):
    if override_name:
        ai_profile.ai_name = override_name
    if override_role:
        ai_profile.ai_role = override_role

    if replace_directives:
        if resources:
            directives.resources = resources
        if constraints:
            directives.constraints = constraints
        if best_practices:
            directives.best_practices = best_practices
    else:
        if resources:
            directives.resources += resources
        if constraints:
            directives.constraints += constraints
        if best_practices:
            directives.best_practices += best_practices