def model_admin(model, model_admin, admin_site=site):
    try:
        org_admin = admin_site.get_model_admin(model)
    except NotRegistered:
        org_admin = None
    else:
        admin_site.unregister(model)
    admin_site.register(model, model_admin)
    try:
        yield
    finally:
        if org_admin:
            admin_site._registry[model] = org_admin