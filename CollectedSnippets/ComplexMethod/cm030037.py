def _getmember(self, name, tarinfo=None, normalize=False):
        """Find an archive member by name from bottom to top.
           If tarinfo is given, it is used as the starting point.
        """
        # Ensure that all members have been loaded.
        members = self.getmembers()

        # Limit the member search list up to tarinfo.
        skipping = False
        if tarinfo is not None:
            try:
                index = members.index(tarinfo)
            except ValueError:
                # The given starting point might be a (modified) copy.
                # We'll later skip members until we find an equivalent.
                skipping = True
            else:
                # Happy fast path
                members = members[:index]

        if normalize:
            name = os.path.normpath(name)

        for member in reversed(members):
            if skipping:
                if tarinfo.offset == member.offset:
                    skipping = False
                continue
            if normalize:
                member_name = os.path.normpath(member.name)
            else:
                member_name = member.name

            if name == member_name:
                return member

        if skipping:
            # Starting point was not found
            raise ValueError(tarinfo)