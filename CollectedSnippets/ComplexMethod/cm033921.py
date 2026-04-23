def _fixup_perms2(self, remote_paths, remote_user=None, execute=True):
        """
        We need the files we upload to be readable (and sometimes executable)
        by the user being sudo'd to but we want to limit other people's access
        (because the files could contain passwords or other private
        information.  We achieve this in one of these ways:

        * If no sudo is performed or the remote_user is sudo'ing to
          themselves, we don't have to change permissions.
        * If the remote_user sudo's to a privileged user (for instance, root),
          we don't have to change permissions
        * If the remote_user sudo's to an unprivileged user then we attempt to
          grant the unprivileged user access via file system acls.
        * If granting file system acls fails we try to change the owner of the
          file with chown which only works in case the remote_user is
          privileged or the remote systems allows chown calls by unprivileged
          users (e.g. HP-UX)
        * If the above fails, we next try 'chmod +a' which is a macOS way of
          setting ACLs on files.
        * If the above fails, we check if ansible_common_remote_group is set.
          If it is, we attempt to chgrp the file to its value. This is useful
          if the remote_user has a group in common with the become_user. As the
          remote_user, we can chgrp the file to that group and allow the
          become_user to read it.
        * If (the chown fails AND ansible_common_remote_group is not set) OR
          (ansible_common_remote_group is set AND the chgrp (or following chmod)
          returned non-zero), we can set the file to be world readable so that
          the second unprivileged user can read the file.
          Since this could allow other users to get access to private
          information we only do this if ansible is configured with
          "allow_world_readable_tmpfiles" in the ansible.cfg. Also note that
          when ansible_common_remote_group is set this final fallback is very
          unlikely to ever be triggered, so long as chgrp was successful. But
          just because the chgrp was successful, does not mean Ansible can
          necessarily access the files (if, for example, the variable was set
          to a group that remote_user is in, and can chgrp to, but does not have
          in common with become_user).
        """
        if remote_user is None:
            remote_user = self._get_remote_user()

        # Step 1: Are we on windows?
        if getattr(self._connection._shell, "_IS_WINDOWS", False):
            # This won't work on Powershell as-is, so we'll just completely
            # skip until we have a need for it, at which point we'll have to do
            # something different.
            return remote_paths

        # Step 2: If we're not becoming an unprivileged user, we are roughly
        # done. Make the files +x if we're asked to, and return.
        if not self._is_become_unprivileged():
            if execute:
                # Can't depend on the file being transferred with required permissions.
                # Only need user perms because no become was used here
                res = self._remote_chmod(remote_paths, 'u+rwx')
                if res['rc'] != 0:
                    raise AnsibleError(
                        'Failed to set permissions on remote files '
                        '(rc: {0}, err: {1})'.format(
                            res['rc'],
                            to_native(res['stderr'])))
            return remote_paths

        # If we're still here, we have an unprivileged user that's different
        # than the ssh user.
        become_user = self.get_become_option('become_user')

        # Try to use file system acls to make the files readable for sudo'd
        # user
        if execute:
            chmod_mode = 'rx'
            setfacl_mode = 'r-x'
            # Apple patches their "file_cmds" chmod with ACL support
            chmod_acl_mode = '{0} allow read,execute'.format(become_user)
            # POSIX-draft ACL specification. Solaris, maybe others.
            # See chmod(1) on something Solaris-based for syntax details.
            posix_acl_mode = 'A+user:{0}:rx:allow'.format(become_user)
        else:
            chmod_mode = 'rX'
            # TODO: this form fails silently on freebsd.  We currently
            # never call _fixup_perms2() with execute=False but if we
            # start to we'll have to fix this.
            setfacl_mode = 'r-X'
            # Apple
            chmod_acl_mode = '{0} allow read'.format(become_user)
            # POSIX-draft
            posix_acl_mode = 'A+user:{0}:r:allow'.format(become_user)

        # Step 3a: Are we able to use setfacl to add user ACLs to the file?
        res = self._remote_set_user_facl(
            remote_paths,
            become_user,
            setfacl_mode)

        match res.get('rc'):
            case 0:
                return remote_paths
            case 2:
                # invalid syntax (for example, missing user, missing colon)
                self._display.debug(f"setfacl command failed with an invalid syntax. Trying chmod instead. Err: {res!r}")
            case 127:
                # setfacl binary does not exists or we don't have permission to use it.
                self._display.debug(f"setfacl binary does not exist or does not have permission to use it. Trying chmod instead. Err: {res!r}")
            case _:
                # generic debug message
                self._display.debug(f'Failed to set facl {setfacl_mode}, got:{res!r}')

        # Step 3b: Set execute if we need to. We do this before anything else
        # because some of the methods below might work but not let us set
        # permissions as part of them.
        if execute:
            res = self._remote_chmod(remote_paths, 'u+rwx')
            if res['rc'] != 0:
                raise AnsibleError(
                    'Failed to set file mode or acl on remote temporary files '
                    '(rc: {0}, err: {1})'.format(
                        res['rc'],
                        to_native(res['stderr'])))

        # Step 3c: File system ACLs failed above; try falling back to chown.
        res = self._remote_chown(remote_paths, become_user)
        if res['rc'] == 0:
            return remote_paths

        # Check if we are an admin/root user. If we are and got here, it means
        # we failed to chown as root and something weird has happened.
        if remote_user in self._get_admin_users():
            raise AnsibleError(
                'Failed to change ownership of the temporary files Ansible '
                '(via chmod nor setfacl) needs to create despite connecting as a '
                'privileged user. Unprivileged become user would be unable to read'
                ' the file.')

        # Step 3d: Try macOS's special chmod + ACL
        # macOS chmod's +a flag takes its own argument. As a slight hack, we
        # pass that argument as the first element of remote_paths. So we end
        # up running `chmod +a [that argument] [file 1] [file 2] ...`
        try:
            res = self._remote_chmod([chmod_acl_mode] + list(remote_paths), '+a')
        except AnsibleAuthenticationFailure as e:
            # Solaris-based chmod will return 5 when it sees an invalid mode,
            # and +a is invalid there. Because it returns 5, which is the same
            # thing sshpass returns on auth failure, our sshpass code will
            # assume that auth failed. If we don't handle that case here, none
            # of the other logic below will get run. This is fairly hacky and a
            # corner case, but probably one that shows up pretty often in
            # Solaris-based environments (and possibly others).
            pass
        else:
            if res['rc'] == 0:
                return remote_paths

        # Step 3e: Try Solaris/OpenSolaris/OpenIndiana-sans-setfacl chmod
        # Similar to macOS above, Solaris 11.4 drops setfacl and takes file ACLs
        # via chmod instead. OpenSolaris and illumos-based distros allow for
        # using either setfacl or chmod, and compatibility depends on filesystem.
        # It should be possible to debug this branch by installing OpenIndiana
        # (use ZFS) and going unpriv -> unpriv.
        res = self._remote_chmod(remote_paths, posix_acl_mode)
        if res['rc'] == 0:
            return remote_paths

        # we'll need this down here
        become_link = get_versioned_doclink('playbook_guide/playbooks_privilege_escalation.html')
        # Step 3f: Common group
        # Otherwise, we're a normal user. We failed to chown the paths to the
        # unprivileged user, but if we have a common group with them, we should
        # be able to chown it to that.
        #
        # Note that we have no way of knowing if this will actually work... just
        # because chgrp exits successfully does not mean that Ansible will work.
        # We could check if the become user is in the group, but this would
        # create an extra round trip.
        #
        # Also note that due to the above, this can prevent the
        # world_readable_temp logic below from ever getting called. We
        # leave this up to the user to rectify if they have both of these
        # features enabled.
        group = self.get_shell_option('common_remote_group')
        if group is not None:
            res = self._remote_chgrp(remote_paths, group)
            if res['rc'] == 0:
                # warn user that something might go weirdly here.
                if self.get_shell_option('world_readable_temp'):
                    display.warning(
                        'Both common_remote_group and '
                        'allow_world_readable_tmpfiles are set. chgrp was '
                        'successful, but there is no guarantee that Ansible '
                        'will be able to read the files after this operation, '
                        'particularly if common_remote_group was set to a '
                        'group of which the unprivileged become user is not a '
                        'member. In this situation, '
                        'allow_world_readable_tmpfiles is a no-op. See this '
                        'URL for more details: %s'
                        '#risks-of-becoming-an-unprivileged-user' % become_link)
                if execute:
                    group_mode = 'g+rwx'
                else:
                    group_mode = 'g+rw'
                res = self._remote_chmod(remote_paths, group_mode)
                if res['rc'] == 0:
                    return remote_paths

        # Step 4: World-readable temp directory
        if self.get_shell_option('world_readable_temp'):
            # chown and fs acls failed -- do things this insecure way only if
            # the user opted in in the config file
            display.warning(
                'Using world-readable permissions for temporary files Ansible '
                'needs to create when becoming an unprivileged user. This may '
                'be insecure. For information on securing this, see %s'
                '#risks-of-becoming-an-unprivileged-user' % become_link)
            res = self._remote_chmod(remote_paths, 'a+%s' % chmod_mode)
            if res['rc'] == 0:
                return remote_paths
            raise AnsibleError(
                'Failed to set file mode on remote files '
                '(rc: {0}, err: {1})'.format(
                    res['rc'],
                    to_native(res['stderr'])))

        raise AnsibleError(
            'Failed to set permissions on the temporary files Ansible needs '
            'to create when becoming an unprivileged user '
            '(rc: %s, err: %s}). For information on working around this, see %s'
            '#risks-of-becoming-an-unprivileged-user' % (
                res['rc'],
                to_native(res['stderr']), become_link))