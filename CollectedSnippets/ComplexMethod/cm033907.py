def unique(environment, a, case_sensitive=None, attribute=None):

    def _do_fail(ex):
        if case_sensitive is False or attribute:
            raise AnsibleError(
                "Jinja2's unique filter failed and we cannot fall back to Ansible's version as it does not support the parameters supplied."
            ) from ex

    error = e = None
    try:
        if HAS_UNIQUE:
            c = list(do_unique(environment, a, case_sensitive=bool(case_sensitive), attribute=attribute))
    except TypeError as e:
        error = e
        _do_fail(e)
    except Exception as e:
        error = e
        _do_fail(e)
        display.error_as_warning('Falling back to Ansible unique filter as Jinja2 one failed.', e)

    if not HAS_UNIQUE or error:

        # handle Jinja2 specific attributes when using Ansible's version
        if case_sensitive is False or attribute:
            raise AnsibleError("Ansible's unique filter does not support case_sensitive=False nor attribute parameters, "
                               "you need a newer version of Jinja2 that provides their version of the filter.")

        c = []
        for x in a:
            if x not in c:
                c.append(x)

    return c