def mysql_version(self):
        match = server_version_re.match(self.mysql_server_info)
        if not match:
            raise Exception(
                "Unable to determine MySQL version from version string %r"
                % self.mysql_server_info
            )
        return tuple(int(x) for x in match.groups())