def parse_django_admin_node(env, sig, signode):
    command = sig.split(" ")[0]
    env.ref_context["std:program"] = command
    title = "django-admin %s" % sig
    signode += addnodes.desc_name(title, title)
    return command