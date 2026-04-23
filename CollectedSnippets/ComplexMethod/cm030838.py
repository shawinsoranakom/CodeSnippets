def get_excepted_output(self, *args):
        if len(args) == 0:
            user_base = site.getuserbase()
            user_site = site.getusersitepackages()
            output = io.StringIO()
            output.write("sys.path = [\n")
            for dir in sys.path:
                output.write("    %r,\n" % (dir,))
            output.write("]\n")
            output.write(f"USER_BASE: {user_base} ({self.exists(user_base)})\n")
            output.write(f"USER_SITE: {user_site} ({self.exists(user_site)})\n")
            output.write(f"ENABLE_USER_SITE: {site.ENABLE_USER_SITE}\n")
            return 0, dedent(output.getvalue()).strip()

        buffer = []
        if '--user-base' in args:
            buffer.append(site.getuserbase())
        if '--user-site' in args:
            buffer.append(site.getusersitepackages())

        if buffer:
            return_code = 3
            if site.ENABLE_USER_SITE:
                return_code = 0
            elif site.ENABLE_USER_SITE is False:
                return_code = 1
            elif site.ENABLE_USER_SITE is None:
                return_code = 2
            output = os.pathsep.join(buffer)
            return return_code, os.path.normpath(dedent(output).strip())
        else:
            return 10, None