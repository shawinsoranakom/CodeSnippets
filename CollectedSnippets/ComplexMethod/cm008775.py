def __contains__(self, target: ImpersonateTarget):
        if not isinstance(target, ImpersonateTarget):
            return False
        return (
            (self.client is None or target.client is None or self.client == target.client)
            and (self.version is None or target.version is None or self.version == target.version)
            and (self.os is None or target.os is None or self.os == target.os)
            and (self.os_version is None or target.os_version is None or self.os_version == target.os_version)
        )