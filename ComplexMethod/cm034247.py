def clean_facts(facts: Mapping[str, object]):
    """ remove facts that can override internal keys or otherwise deemed unsafe """
    data = module_response_deepcopy(facts)

    remove_keys = set()
    fact_keys = set(data.keys())
    # first we add all of our magic variable names to the set of
    # keys we want to remove from facts
    # NOTE: these will eventually disappear in favor of others below
    for magic_var in C.MAGIC_VARIABLE_MAPPING:
        remove_keys.update(fact_keys.intersection(C.MAGIC_VARIABLE_MAPPING[magic_var]))

    # remove common connection vars
    remove_keys.update(fact_keys.intersection(C.COMMON_CONNECTION_VARS))

    # next we remove any connection plugin specific vars
    for conn_path in connection_loader.all(path_only=True):
        conn_name = os.path.splitext(os.path.basename(conn_path))[0]
        re_key = re.compile('^ansible_%s_' % re.escape(conn_name))
        for fact_key in fact_keys:
            # most lightweight VM or container tech creates devices with this pattern, this avoids filtering them out
            if (re_key.match(fact_key) and not fact_key.endswith(('_bridge', '_gwbridge'))) or fact_key.startswith('ansible_become_'):
                remove_keys.add(fact_key)

    # remove some KNOWN keys
    for hard in C.RESTRICTED_RESULT_KEYS:
        if hard in fact_keys:
            remove_keys.add(hard)

    # finally, we search for interpreter keys to remove
    re_interp = re.compile('^ansible_.*_interpreter$')
    for fact_key in fact_keys:
        if re_interp.match(fact_key):
            remove_keys.add(fact_key)
    # then we remove them (except for ssh host keys)
    for r_key in remove_keys:
        if not r_key.startswith('ansible_ssh_host_key_'):
            display.warning("Removed restricted key from module data: %s" % (r_key))
            del data[r_key]

    return strip_internal_keys(data)