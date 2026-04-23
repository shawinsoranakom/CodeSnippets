def _run(self, tmp=None, task_vars=None):
        """ handler for file transfer operations """
        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)

        del tmp  # tmp no longer has any effect

        # ensure user is not setting internal parameters
        for internal in ('_original_basename', '_diff_peek'):
            if self._task.args.get(internal, None) is not None:
                raise AnsibleActionFail(f'Invalid parameter specified: "{internal}"')

        source = self._task.args.get('src', None)
        content = self._task.args.get('content', None)
        dest = self._task.args.get('dest', None)
        remote_src = boolean(self._task.args.get('remote_src', False), strict=False)
        local_follow = boolean(self._task.args.get('local_follow', True), strict=False)

        result['failed'] = True
        if not source and content is None:
            result['msg'] = 'src (or content) is required'
        elif not dest:
            result['msg'] = 'dest is required'
        elif source and content is not None:
            result['msg'] = 'src and content are mutually exclusive'
        elif content is not None and dest is not None and dest.endswith("/"):
            result['msg'] = "can not use content with a dir as dest"
        else:
            del result['failed']

        if result.get('failed'):
            return result

        # Define content_tempfile in case we set it after finding content populated.
        content_tempfile = None

        # If content is defined make a tmp file and write the content into it.
        if content is not None:
            try:
                # If content comes to us as a dict it should be decoded json.
                # We need to encode it back into a string to write it out.
                if isinstance(content, dict) or isinstance(content, list):
                    content_tempfile = self._create_content_tempfile(json.dumps(content))
                else:
                    content_tempfile = self._create_content_tempfile(content)
                source = content_tempfile
            except Exception as ex:
                raise AnsibleActionFail(message="could not write content temp file", result=result) from ex

        # if we have first_available_file in our vars
        # look up the files and use the first one we find as src
        elif remote_src:
            result.update(self._execute_module(module_name='ansible.legacy.copy', task_vars=task_vars))
            return result
        else:
            # find_needle returns a path that may not have a trailing slash on
            # a directory so we need to determine that now (we use it just
            # like rsync does to figure out whether to include the directory
            # or only the files inside the directory
            trailing_slash = source.endswith(os.path.sep)
            try:
                # find in expected paths
                source = self._find_needle('files', source)
            except AnsibleError as ex:
                raise AnsibleActionFail(result=result) from ex

            if trailing_slash != source.endswith(os.path.sep):
                if source[-1] == os.path.sep:
                    source = source[:-1]
                else:
                    source = source + os.path.sep

        # A list of source file tuples (full_path, relative_path) which will try to copy to the destination
        source_files = {'files': [], 'directories': [], 'symlinks': []}

        # If source is a directory populate our list else source is a file and translate it to a tuple.
        if os.path.isdir(to_bytes(source, errors='surrogate_or_strict')):
            # Get a list of the files we want to replicate on the remote side
            source_files = _walk_dirs(source, local_follow=local_follow,
                                      trailing_slash_detector=self._connection._shell.path_has_trailing_slash)

            # If it's recursive copy, destination is always a dir,
            # explicitly mark it so (note - copy module relies on this).
            if not self._connection._shell.path_has_trailing_slash(dest):
                dest = self._connection._shell.join_path(dest, '')
            # FIXME: Can we optimize cases where there's only one file, no
            # symlinks and any number of directories?  In the original code,
            # empty directories are not copied....
        else:
            source_files['files'] = [(source, os.path.basename(source))]

        changed = False
        module_return = dict(changed=False)

        # A register for if we executed a module.
        # Used to cut down on command calls when not recursive.
        module_executed = False

        # expand any user home dir specifier
        dest = self._remote_expand_user(dest)

        implicit_directories = set()
        for source_full, source_rel in source_files['files']:
            # copy files over.  This happens first as directories that have
            # a file do not need to be created later

            # We only follow symlinks for files in the non-recursive case
            if source_files['directories']:
                follow = False
            else:
                follow = boolean(self._task.args.get('follow', False), strict=False)

            module_return = self._copy_file(source_full, source_rel, content, content_tempfile, dest, task_vars, follow)
            if module_return is None:
                continue

            if module_return.get('failed'):
                result.update(module_return)
                return result

            while (source_rel := os.path.dirname(source_rel)) != '':
                implicit_directories.add(source_rel)

            if 'diff' in result and not result['diff']:
                del result['diff']
            module_executed = True
            changed = changed or module_return.get('changed', False)

        for src, dest_path in source_files['directories']:
            # Find directories that are leaves as they might not have been
            # created yet.
            if dest_path in implicit_directories:
                continue

            # Use file module to create these
            new_module_args = _create_remote_file_args(self._task.args)
            new_module_args['path'] = os.path.join(dest, dest_path)
            new_module_args['state'] = 'directory'
            new_module_args['mode'] = self._task.args.get('directory_mode', None)
            new_module_args['recurse'] = False
            del new_module_args['src']

            module_return = self._execute_module(module_name='ansible.legacy.file', module_args=new_module_args, task_vars=task_vars)

            if module_return.get('failed'):
                result.update(module_return)
                return result

            module_executed = True
            changed = changed or module_return.get('changed', False)

        for target_path, dest_path in source_files['symlinks']:
            # Copy symlinks over
            new_module_args = _create_remote_file_args(self._task.args)
            new_module_args['path'] = os.path.join(dest, dest_path)
            new_module_args['src'] = target_path
            new_module_args['state'] = 'link'
            new_module_args['force'] = True

            # Only follow remote symlinks in the non-recursive case
            if source_files['directories']:
                new_module_args['follow'] = False

            # file module cannot deal with 'preserve' mode and is meaningless
            # for symlinks anyway, so just don't pass it.
            if new_module_args.get('mode', None) == 'preserve':
                new_module_args.pop('mode')

            module_return = self._execute_module(module_name='ansible.legacy.file', module_args=new_module_args, task_vars=task_vars)
            module_executed = True

            if module_return.get('failed'):
                result.update(module_return)
                return result

            changed = changed or module_return.get('changed', False)

        if module_executed and len(source_files['files']) == 1:
            result.update(module_return)

            # the file module returns the file path as 'path', but
            # the copy module uses 'dest', so add it if it's not there
            if 'path' in result and 'dest' not in result:
                result['dest'] = result['path']
        else:
            result.update(dict(dest=dest, src=source, changed=changed))

        # Delete tmp path
        self._remove_tmp_path(self._connection._shell.tmpdir)

        return result