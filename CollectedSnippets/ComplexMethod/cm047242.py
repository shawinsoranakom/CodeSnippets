def has_groups(self, group_spec: str) -> bool:
        """ Return whether user ``self`` satisfies the given group restrictions
        ``group_spec``, i.e., whether it is member of at least one of the groups,
        and is not a member of any of the groups preceded by ``!``.

        Note that the group ``"base.group_no_one"`` is only effective in debug
        mode, just like method :meth:`~.has_group` does.

        :param str group_spec: comma-separated list of fully-qualified group
            external IDs, optionally preceded by ``!``.
            Example:``"base.group_user,base.group_portal,!base.group_system"``.
        """
        if group_spec == '.':
            return False

        positives = []
        negatives = []
        for group_ext_id in group_spec.split(','):
            group_ext_id = group_ext_id.strip()
            if group_ext_id.startswith('!'):
                negatives.append(group_ext_id[1:])
            else:
                positives.append(group_ext_id)

        # for the sake of performance, check negatives first
        if any(self.has_group(ext_id) for ext_id in negatives):
            return False
        if any(self.has_group(ext_id) for ext_id in positives):
            return True
        return not positives