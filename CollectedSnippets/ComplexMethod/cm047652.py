def save(self, keys=None):
        p = ConfigParser.RawConfigParser()
        rc_exists = os.path.exists(self['config'])
        if rc_exists and keys:
            p.read([self['config']])
        if not p.has_section('options'):
            p.add_section('options')
        for opt in sorted(self.options):
            option = self.options_index.get(opt)
            if keys is not None and opt not in keys:
                continue
            if opt == 'version' or (option and not option.file_exportable):
                continue
            if option:
                p.set('options', opt, self.format(opt, self.options[opt]))
            else:
                p.set('options', opt, self.options[opt])

        # try to create the directories and write the file
        try:
            if not rc_exists and not os.path.exists(os.path.dirname(self['config'])):
                os.makedirs(os.path.dirname(self['config']))
            try:
                with open(self['config'], 'w', encoding='utf-8') as file:
                    p.write(file)
                if not rc_exists:
                    os.chmod(self['config'], 0o600)
            except IOError:
                sys.stderr.write("ERROR: couldn't write the config file\n")

        except OSError:
            # what to do if impossible?
            sys.stderr.write("ERROR: couldn't create the config directory\n")