def __init__(self, module):
        self.module = module
        self.state = module.params['state']
        self.name = module.params['name']
        self.uid = module.params['uid']
        self.hidden = module.params['hidden']
        self.non_unique = module.params['non_unique']
        self.seuser = module.params['seuser']
        self.group = module.params['group']
        self.comment = module.params['comment']
        self.shell = module.params['shell']
        self.password = module.params['password']
        self.force = module.params['force']
        self.remove = module.params['remove']
        self.create_home = module.params['create_home']
        self.move_home = module.params['move_home']
        self.skeleton = module.params['skeleton']
        self.system = module.params['system']
        self.login_class = module.params['login_class']
        self.append = module.params['append']
        self.sshkeygen = module.params['generate_ssh_key']
        self.ssh_bits = module.params['ssh_key_bits']
        self.ssh_type = module.params['ssh_key_type']
        self.ssh_comment = module.params['ssh_key_comment']
        self.ssh_passphrase = module.params['ssh_key_passphrase']
        self.update_password = module.params['update_password']
        self.home = module.params['home']
        self.expires = None
        self.password_lock = module.params['password_lock']
        self.groups = None
        self.local = module.params['local']
        self.profile = module.params['profile']
        self.authorization = module.params['authorization']
        self.role = module.params['role']
        self.password_expire_max = module.params['password_expire_max']
        self.password_expire_min = module.params['password_expire_min']
        self.password_expire_warn = module.params['password_expire_warn']
        self.umask = module.params['umask']
        self.inactive = module.params['password_expire_account_disable']
        self.uid_min = module.params['uid_min']
        self.uid_max = module.params['uid_max']

        if self.local:
            if self.umask is not None:
                module.fail_json(msg="'umask' can not be used with 'local'")
            if self.uid_min is not None:
                module.fail_json(msg="'uid_min' can not be used with 'local'")
            if self.uid_max is not None:
                module.fail_json(msg="'uid_max' can not be used with 'local'")

        if module.params['groups'] is not None:
            self.groups = ','.join(module.params['groups'])

        if module.params['expires'] is not None:
            try:
                self.expires = time.gmtime(module.params['expires'])
            except Exception as e:
                module.fail_json(msg="Invalid value for 'expires' %s: %s" % (self.expires, to_native(e)))

        if module.params['ssh_key_file'] is not None:
            self.ssh_file = module.params['ssh_key_file']
        else:
            self.ssh_file = os.path.join('.ssh', 'id_%s' % self.ssh_type)