def main():
    argument_spec = dict(
        bandwidth=dict(),
        baseurl=dict(type='list', elements='str'),
        cost=dict(),
        countme=dict(type='bool'),
        deltarpm_percentage=dict(),
        description=dict(),
        enabled=dict(type='bool'),
        enablegroups=dict(type='bool'),
        exclude=dict(type='list', elements='str', aliases=['excludepkgs']),
        failovermethod=dict(choices=['roundrobin', 'priority']),
        file=dict(),
        gpgcheck=dict(type='bool'),
        gpgkey=dict(type='list', elements='str', no_log=False),
        module_hotfixes=dict(type='bool'),
        include=dict(),
        includepkgs=dict(type='list', elements='str'),
        ip_resolve=dict(choices=['4', '6', 'IPv4', 'IPv6', 'whatever']),
        metadata_expire=dict(),
        metalink=dict(),
        mirrorlist=dict(),
        name=dict(required=True),
        password=dict(no_log=True),
        priority=dict(),
        proxy=dict(),
        proxy_password=dict(no_log=True),
        proxy_username=dict(),
        repo_gpgcheck=dict(type='bool'),
        reposdir=dict(default='/etc/yum.repos.d', type='path'),
        retries=dict(),
        s3_enabled=dict(type='bool'),
        skip_if_unavailable=dict(type='bool'),
        sslcacert=dict(aliases=['ca_cert']),
        sslclientcert=dict(aliases=['client_cert']),
        sslclientkey=dict(aliases=['client_key'], no_log=False),
        sslverify=dict(type='bool', aliases=['validate_certs']),
        state=dict(choices=['present', 'absent'], default='present'),
        throttle=dict(),
        timeout=dict(),
        username=dict(),
    )

    module = AnsibleModule(
        required_if=[
            ["state", "present", ["baseurl", "mirrorlist", "metalink"], True],
            ["state", "present", ["description"]],
        ],
        argument_spec=argument_spec,
        add_file_common_args=True,
        supports_check_mode=True,
    )

    # make copy of params as we need to split them into yum repo only and file params
    yum_repo_params = module.params.copy()
    for alias in module.aliases:
        yum_repo_params.pop(alias, None)

    file_common_params = {}
    for param in FILE_COMMON_ARGUMENTS:
        file_common_params[param] = yum_repo_params.pop(param)

    state = yum_repo_params.pop("state")
    name = yum_repo_params['name']
    yum_repo_params['name'] = yum_repo_params.pop('description')

    for list_param in ('baseurl', 'gpgkey'):
        v = yum_repo_params[list_param]
        if v is not None:
            yum_repo_params[list_param] = '\n'.join(v)

    for list_param in ('exclude', 'includepkgs'):
        v = yum_repo_params[list_param]
        if v is not None:
            yum_repo_params[list_param] = ' '.join(v)

    repos_dir = yum_repo_params.pop("reposdir")
    if not os.path.isdir(repos_dir):
        module.fail_json(
            msg="Repo directory '%s' does not exist." % repos_dir
        )

    if (file := yum_repo_params.pop("file")) is None:
        file = name
    file_common_params["dest"] = os.path.join(repos_dir, f"{file}.repo")

    yumrepo = YumRepo(module, yum_repo_params, name, file_common_params["dest"])

    diff = {
        'before_header': file_common_params["dest"],
        'before': yumrepo.dump(),
        'after_header': file_common_params["dest"],
        'after': ''
    }

    if state == 'present':
        yumrepo.add()
    elif state == 'absent':
        yumrepo.remove()

    diff['after'] = yumrepo.dump()

    changed = diff['before'] != diff['after']

    if not module.check_mode and changed:
        yumrepo.save()

    if os.path.isfile(file_common_params["dest"]):
        file_args = module.load_file_common_arguments(file_common_params)
        changed = module.set_fs_attributes_if_different(file_args, changed)

    module.exit_json(changed=changed, repo=name, state=state, diff=diff)