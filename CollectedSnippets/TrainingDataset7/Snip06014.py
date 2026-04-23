def user_has_model_view_permission(user, opts):
    """Based off ModelAdmin.has_view_permission."""
    codename_view = get_permission_codename("view", opts)
    codename_change = get_permission_codename("change", opts)
    return user.has_perm("%s.%s" % (opts.app_label, codename_view)) or user.has_perm(
        "%s.%s" % (opts.app_label, codename_change)
    )