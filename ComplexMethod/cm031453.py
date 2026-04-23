def GetUserCfgDir(self):
        """Return a filesystem directory for storing user config files.

        Creates it if required.
        """
        cfgDir = '.idlerc'
        userDir = os.path.expanduser('~')
        if userDir != '~': # expanduser() found user home dir
            if not os.path.exists(userDir):
                if not idlelib.testing:
                    warn = ('\n Warning: os.path.expanduser("~") points to\n ' +
                            userDir + ',\n but the path does not exist.')
                    try:
                        print(warn, file=sys.stderr)
                    except OSError:
                        pass
                userDir = '~'
        if userDir == "~": # still no path to home!
            # traditionally IDLE has defaulted to os.getcwd(), is this adequate?
            userDir = os.getcwd()
        userDir = os.path.join(userDir, cfgDir)
        if not os.path.exists(userDir):
            try:
                os.mkdir(userDir)
            except OSError:
                if not idlelib.testing:
                    warn = ('\n Warning: unable to create user config directory\n' +
                            userDir + '\n Check path and permissions.\n Exiting!\n')
                    try:
                        print(warn, file=sys.stderr)
                    except OSError:
                        pass
                raise SystemExit
        # TODO continue without userDIr instead of exit
        return userDir