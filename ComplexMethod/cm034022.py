def load_file_common_arguments(self, params, path=None):
        """
        many modules deal with files, this encapsulates common
        options that the file module accepts such that it is directly
        available to all modules and they can share code.

        Allows to overwrite the path/dest module argument by providing path.
        """

        if path is None:
            path = params.get('path', params.get('dest', None))
        if path is None:
            return {}
        else:
            path = os.path.expanduser(os.path.expandvars(path))

        b_path = to_bytes(path, errors='surrogate_or_strict')
        # if the path is a symlink, and we're following links, get
        # the target of the link instead for testing
        if params.get('follow', False) and os.path.islink(b_path):
            b_path = os.path.realpath(b_path)
            path = to_native(b_path)

        mode = params.get('mode', None)
        owner = params.get('owner', None)
        group = params.get('group', None)

        # selinux related options
        seuser = params.get('seuser', None)
        serole = params.get('serole', None)
        setype = params.get('setype', None)
        selevel = params.get('selevel', None)
        secontext = [seuser, serole, setype]

        if self.selinux_mls_enabled():
            secontext.append(selevel)

        default_secontext = self.selinux_default_context(path)
        for i in range(len(default_secontext)):
            if i is not None and secontext[i] == '_default':
                secontext[i] = default_secontext[i]

        attributes = params.get('attributes', None)
        return dict(
            path=path, mode=mode, owner=owner, group=group,
            seuser=seuser, serole=serole, setype=setype,
            selevel=selevel, secontext=secontext, attributes=attributes,
        )