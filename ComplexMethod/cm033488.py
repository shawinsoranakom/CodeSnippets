def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default="present", choices=["present", "latest", "absent"], required=False),
            name=dict(aliases=["pkg"], required=True, type='list'),
            cached=dict(default=False, type='bool'),
            annotation=dict(default="", required=False),
            pkgsite=dict(default="", required=False),
            rootdir=dict(default="", required=False, type='path'),
            chroot=dict(default="", required=False, type='path'),
            jail=dict(default="", required=False, type='str'),
            autoremove=dict(default=False, type='bool')),
        supports_check_mode=True,
        mutually_exclusive=[["rootdir", "chroot", "jail"]])

    pkgng_path = module.get_bin_path('pkg', True)

    p = module.params

    pkgs = p["name"]

    changed = False
    msgs = []
    dir_arg = ""

    if p["rootdir"] != "":
        old_pkgng = pkgng_older_than(module, pkgng_path, [1, 5, 0])
        if old_pkgng:
            module.fail_json(msg="To use option 'rootdir' pkg version must be 1.5 or greater")
        else:
            dir_arg = "--rootdir %s" % (p["rootdir"])

    if p["chroot"] != "":
        dir_arg = '--chroot %s' % (p["chroot"])

    if p["jail"] != "":
        dir_arg = '--jail %s' % (p["jail"])

    if p["state"] in ("present", "latest"):
        _changed, _msg = install_packages(module, pkgng_path, pkgs, p["cached"], p["pkgsite"], dir_arg, p["state"])
        changed = changed or _changed
        msgs.append(_msg)

    elif p["state"] == "absent":
        _changed, _msg = remove_packages(module, pkgng_path, pkgs, dir_arg)
        changed = changed or _changed
        msgs.append(_msg)

    if p["autoremove"]:
        _changed, _msg = autoremove_packages(module, pkgng_path, dir_arg)
        changed = changed or _changed
        msgs.append(_msg)

    if p["annotation"]:
        _changed, _msg = annotate_packages(module, pkgng_path, pkgs, p["annotation"], dir_arg)
        changed = changed or _changed
        msgs.append(_msg)

    module.exit_json(changed=changed, msg=", ".join(msgs))