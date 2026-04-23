def install(self):

        if self.scm:
            # create tar file from scm url
            tmp_file = RoleRequirement.scm_archive_role(keep_scm_meta=context.CLIARGS['keep_scm_meta'], **self.spec)
        elif self.src:
            if os.path.isfile(self.src):
                tmp_file = self.src
            elif '://' in self.src:
                role_data = self.src
                tmp_file = self.fetch(role_data)
            else:
                role_data = self.api.lookup_role_by_name(self.src)
                if not role_data:
                    raise AnsibleError("- sorry, %s was not found on %s." % (self.src, self.api.api_server))

                if role_data.get('role_type') == 'APP':
                    # Container Role
                    display.warning("%s is a Container App role, and should only be installed using Ansible "
                                    "Container" % self.name)

                role_versions = self.api.fetch_role_related('versions', role_data['id'])
                if not self.version:
                    # convert the version names to LooseVersion objects
                    # and sort them to get the latest version. If there
                    # are no versions in the list, we'll grab the head
                    # of the master branch
                    if len(role_versions) > 0:
                        loose_versions = [v for a in role_versions if (v := LooseVersion()) and v.parse(a.get('name') or '') is None]
                        try:
                            loose_versions.sort()
                        except TypeError:
                            raise AnsibleError(
                                'Unable to compare role versions (%s) to determine the most recent version due to incompatible version formats. '
                                'Please contact the role author to resolve versioning conflicts, or specify an explicit role version to '
                                'install.' % ', '.join([v.vstring for v in loose_versions])
                            )
                        self.version = to_text(loose_versions[-1])
                    elif role_data.get('github_branch', None):
                        self.version = role_data['github_branch']
                    else:
                        self.version = 'master'
                elif self.version != 'master':
                    if role_versions and to_text(self.version) not in [a.get('name', None) for a in role_versions]:
                        raise AnsibleError("- the specified version (%s) of %s was not found in the list of available versions (%s)." % (self.version,
                                                                                                                                         self.name,
                                                                                                                                         role_versions))

                # check if there's a source link/url for our role_version
                for role_version in role_versions:
                    if role_version['name'] == self.version and 'source' in role_version:
                        self.src = role_version['source']
                    if role_version['name'] == self.version and 'download_url' in role_version:
                        self.download_url = role_version['download_url']

                tmp_file = self.fetch(role_data)

        else:
            raise AnsibleError("No valid role data found")

        if tmp_file:

            display.debug("installing from %s" % tmp_file)

            if not tarfile.is_tarfile(tmp_file):
                raise AnsibleError("the downloaded file does not appear to be a valid tar archive.")
            else:
                role_tar_file = tarfile.open(tmp_file, "r")
                # verify the role's meta file
                meta_file = None
                members = role_tar_file.getmembers()
                # next find the metadata file
                for member in members:
                    for meta_main in self.META_MAIN:
                        if meta_main in member.name:
                            # Look for parent of meta/main.yml
                            # Due to possibility of sub roles each containing meta/main.yml
                            # look for shortest length parent
                            meta_parent_dir = os.path.dirname(os.path.dirname(member.name))
                            if not meta_file:
                                archive_parent_dir = meta_parent_dir
                                meta_file = member
                            else:
                                if len(meta_parent_dir) < len(archive_parent_dir):
                                    archive_parent_dir = meta_parent_dir
                                    meta_file = member
                if not meta_file:
                    raise AnsibleError("this role does not appear to have a meta/main.yml file.")
                else:
                    try:
                        self._metadata = yaml_load(role_tar_file.extractfile(meta_file))
                    except Exception:
                        raise AnsibleError("this role does not appear to have a valid meta/main.yml file.")

                paths = self.paths
                if self.path != paths[0]:
                    # path can be passed though __init__
                    # FIXME should this be done in __init__?
                    paths[:0] = self.path
                paths_len = len(paths)
                for idx, path in enumerate(paths):
                    self.path = path
                    display.display("- extracting %s to %s" % (self.name, self.path))
                    try:
                        if os.path.exists(self.path):
                            if not os.path.isdir(self.path):
                                raise AnsibleError("the specified roles path exists and is not a directory.")
                            elif not context.CLIARGS.get("force", False):
                                raise AnsibleError("the specified role %s appears to already exist. Use --force to replace it." % self.name)
                            else:
                                # using --force, remove the old path
                                if not self.remove():
                                    raise AnsibleError("%s doesn't appear to contain a role.\n  please remove this directory manually if you really "
                                                       "want to put the role here." % self.path)
                        else:
                            os.makedirs(self.path)

                        resolved_archive = unfrackpath(archive_parent_dir, follow=False)

                        # We strip off any higher-level directories for all of the files
                        # contained within the tar file here. The default is 'github_repo-target'.
                        # Gerrit instances, on the other hand, does not have a parent directory at all.
                        for member in members:
                            # we only extract files, and remove any relative path
                            # bits that might be in the file for security purposes
                            # and drop any containing directory, as mentioned above
                            if not (member.isreg() or member.issym()):
                                continue

                            for attr in ('name', 'linkname'):
                                if not (attr_value := getattr(member, attr, None)):
                                    continue

                                if attr == 'linkname':
                                    # Symlinks are relative to the link
                                    relative_to = os.path.dirname(getattr(member, 'name', ''))
                                else:
                                    # Normalize paths that start with the archive dir
                                    attr_value = attr_value.replace(archive_parent_dir, "", 1)
                                    attr_value = os.path.join(*attr_value.split(os.sep))  # remove leading os.sep
                                    relative_to = ''

                                full_path = os.path.join(resolved_archive, relative_to, attr_value)
                                if not is_subpath(full_path, resolved_archive, real=True):
                                    err = f"Invalid {attr} for tarfile member: path {full_path} is not a subpath of the role {resolved_archive}"
                                    raise AnsibleError(err)

                                relative_path_dir = os.path.join(resolved_archive, relative_to)
                                relative_path = os.path.join(*full_path.replace(relative_path_dir, "", 1).split(os.sep))
                                setattr(member, attr, relative_path)

                            role_tar_file.extract(member, to_native(self.path), filter='data')

                        # write out the install info file for later use
                        self._write_galaxy_install_info()
                        break
                    except OSError as e:
                        if e.errno == errno.EACCES and idx < paths_len - 1:
                            continue
                        raise AnsibleError("Could not update files in %s: %s" % (self.path, to_native(e)))

                # return the parsed yaml metadata
                display.display("- %s was installed successfully" % str(self))
                if not (self.src and os.path.isfile(self.src)):
                    try:
                        os.unlink(tmp_file)
                    except OSError as ex:
                        display.error_as_warning(f"Unable to remove tmp file {tmp_file!r}.", exception=ex)
                return True

        return False