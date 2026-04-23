def check_admin_app(app_configs, **kwargs):
    from django.contrib.admin.sites import all_sites

    errors = []
    for site in all_sites:
        errors.extend(site.check(app_configs))
    return errors