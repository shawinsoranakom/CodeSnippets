def run(self, tmp=None, task_vars=None):
        """ handler for file transfer operations """
        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        source = self._task.args.get('src', None)
        content = self._task.args.get('content', None)
        dest = self._task.args.get('dest', None)
        remote_src = boolean(self._task.args.get('remote_src', False), strict=False)
        local_follow = boolean(self._task.args.get('local_follow', False), strict=False)
        force = boolean(self._task.args.get('force', True), strict=False)
        decrypt = boolean(self._task.args.get('decrypt', True), strict=False)
        backup = boolean(self._task.args.get('backup', False), strict=False)

        result['src'] = source
        result['dest'] = dest

        result['failed'] = True
        if (source is None and content is None) or dest is None:
            result['msg'] = "src (or content) and dest are required"
        elif source is not None and content is not None:
            result['msg'] = "src and content are mutually exclusive"
        elif content is not None and dest is not None and (
                dest.endswith(os.path.sep) or dest.endswith(self.WIN_PATH_SEPARATOR)):
            result['msg'] = "dest must be a file if content is defined"
        else:
            del result['failed']

        if result.get('failed'):
            return result

        # If content is defined make a temp file and write the content into it
        content_tempfile = None
        if content is not None:
            try:
                # if content comes to us as a dict it should be decoded json.
                # We need to encode it back into a string and write it out
                if isinstance(content, dict) or isinstance(content, list):
                    content_tempfile = self._create_content_tempfile(json.dumps(content))
                else:
                    content_tempfile = self._create_content_tempfile(content)
                source = content_tempfile
            except Exception as err:
                result['failed'] = True
                result['msg'] = "could not write content tmp file: %s" % to_native(err)
                return result
        # all actions should occur on the remote server, run win_copy module
        elif remote_src:
            new_module_args = self._task.args.copy()
            new_module_args.update(
                dict(
                    _copy_mode="remote",
                    dest=dest,
                    src=source,
                    force=force,
                    backup=backup,
                )
            )
            new_module_args.pop('content', None)
            result.update(self._execute_module(module_args=new_module_args, task_vars=task_vars))
            return result
        # find_needle returns a path that may not have a trailing slash on a
        # directory so we need to find that out first and append at the end
        else:
            trailing_slash = source.endswith(os.path.sep)
            try:
                # find in expected paths
                source = self._find_needle('files', source)
            except AnsibleError as e:
                result['failed'] = True
                result['msg'] = to_text(e)
                result['exception'] = traceback.format_exc()
                return result

            if trailing_slash != source.endswith(os.path.sep):
                if source[-1] == os.path.sep:
                    source = source[:-1]
                else:
                    source = source + os.path.sep

        # A list of source file tuples (full_path, relative_path) which will try to copy to the destination
        source_files = {'files': [], 'directories': [], 'symlinks': []}

        # If source is a directory populate our list else source is a file and translate it to a tuple.
        if os.path.isdir(to_bytes(source, errors='surrogate_or_strict')):
            result['operation'] = 'folder_copy'

            # Get a list of the files we want to replicate on the remote side
            source_files = _walk_dirs(source, self._loader, decrypt=decrypt, local_follow=local_follow,
                                      trailing_slash_detector=self._connection._shell.path_has_trailing_slash,
                                      checksum_check=force)

            # If it's recursive copy, destination is always a dir,
            # explicitly mark it so (note - win_copy module relies on this).
            if not self._connection._shell.path_has_trailing_slash(dest):
                dest = "%s%s" % (dest, self.WIN_PATH_SEPARATOR)

            check_dest = dest
        # Source is a file, add details to source_files dict
        else:
            result['operation'] = 'file_copy'

            # If the local file does not exist, get_real_file() raises AnsibleFileNotFound
            try:
                source_full = self._loader.get_real_file(source, decrypt=decrypt)
            except AnsibleFileNotFound as e:
                result['failed'] = True
                result['msg'] = "could not find src=%s, %s" % (source, to_text(e))
                return result

            original_basename = os.path.basename(source)
            result['original_basename'] = original_basename

            # check if dest ends with / or \ and append source filename to dest
            if self._connection._shell.path_has_trailing_slash(dest):
                check_dest = dest
                filename = original_basename
                result['dest'] = self._connection._shell.join_path(dest, filename)
            else:
                # replace \\ with / so we can use os.path to get the filename or dirname
                unix_path = dest.replace(self.WIN_PATH_SEPARATOR, os.path.sep)
                filename = os.path.basename(unix_path)
                check_dest = os.path.dirname(unix_path)

            file_checksum = _get_local_checksum(force, source_full)
            source_files['files'].append(
                dict(
                    src=source_full,
                    dest=filename,
                    checksum=file_checksum
                )
            )
            result['checksum'] = file_checksum
            result['size'] = os.path.getsize(to_bytes(source_full, errors='surrogate_or_strict'))

        # find out the files/directories/symlinks that we need to copy to the server
        query_args = self._task.args.copy()
        query_args.update(
            dict(
                _copy_mode="query",
                dest=check_dest,
                force=force,
                files=source_files['files'],
                directories=source_files['directories'],
                symlinks=source_files['symlinks'],
            )
        )
        # src is not required for query, will fail path validation is src has unix allowed chars
        query_args.pop('src', None)

        query_args.pop('content', None)
        query_return = self._execute_module(module_args=query_args,
                                            task_vars=task_vars)

        if query_return.get('failed') is True:
            result.update(query_return)
            return result

        if len(query_return['files']) > 0 or len(query_return['directories']) > 0 and self._connection._shell.tmpdir is None:
            self._connection._shell.tmpdir = self._make_tmp_path()

        if len(query_return['files']) == 1 and len(query_return['directories']) == 0:
            # we only need to copy 1 file, don't mess around with zips
            file_src = query_return['files'][0]['src']
            file_dest = query_return['files'][0]['dest']
            result.update(self._copy_single_file(file_src, dest, file_dest,
                                                 task_vars, self._connection._shell.tmpdir, backup))
            if result.get('failed') is True:
                result['msg'] = "failed to copy file %s: %s" % (file_src, result['msg'])
            result['changed'] = True

        elif len(query_return['files']) > 0 or len(query_return['directories']) > 0:
            # either multiple files or directories need to be copied, compress
            # to a zip and 'explode' the zip on the server
            # TODO: handle symlinks
            result.update(self._copy_zip_file(dest, source_files['files'],
                                              source_files['directories'],
                                              task_vars, self._connection._shell.tmpdir, backup))
            result['changed'] = True
        else:
            # no operations need to occur
            result['failed'] = False
            result['changed'] = False

        # remove the content tmp file and remote tmp file if it was created
        self._remove_tempfile_if_content_defined(content, content_tempfile)
        self._remove_tmp_path(self._connection._shell.tmpdir)
        return result