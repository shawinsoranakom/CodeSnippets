def _get_diff_data(self, destination, source, task_vars, content=None, source_file=True):

        # Note: Since we do not diff the source and destination before we transform from bytes into
        # text the diff between source and destination may not be accurate.  To fix this, we'd need
        # to move the diffing from the callback plugins into here.
        #
        # Example of data which would cause trouble is src_content == b'\xff' and dest_content ==
        # b'\xfe'.  Neither of those are valid utf-8 so both get turned into the replacement
        # character: diff['before'] = u'�' ; diff['after'] = u'�'  When the callback plugin later
        # diffs before and after it shows an empty diff.

        diff = {}
        display.debug("Going to peek to see if file has changed permissions")
        peek_result = self._execute_module(
            module_name='ansible.legacy.file', module_args=dict(path=destination, _diff_peek=True),
            task_vars=task_vars, persist_files=True)

        if peek_result.get('failed', False):
            display.warning(u"Failed to get diff between '%s' and '%s': %s" % (os.path.basename(source), destination, to_text(peek_result.get(u'msg', u''))))
            return diff

        if peek_result.get('rc', 0) == 0:

            if peek_result.get('state') in (None, 'absent'):
                diff['before'] = u''
            elif peek_result.get('appears_binary'):
                diff['dst_binary'] = 1
            elif peek_result.get('size') and C.MAX_FILE_SIZE_FOR_DIFF > 0 and peek_result['size'] > C.MAX_FILE_SIZE_FOR_DIFF:
                diff['dst_larger'] = C.MAX_FILE_SIZE_FOR_DIFF
            else:
                display.debug(u"Slurping the file %s" % destination)
                dest_result = self._execute_module(
                    module_name='ansible.legacy.slurp', module_args=dict(path=destination),
                    task_vars=task_vars, persist_files=True)
                if 'content' in dest_result:
                    dest_contents = dest_result['content']
                    if dest_result['encoding'] == u'base64':
                        dest_contents = base64.b64decode(dest_contents)
                    else:
                        raise AnsibleError("unknown encoding in content option, failed: %s" % to_native(dest_result))
                    diff['before_header'] = destination
                    diff['before'] = to_text(dest_contents)

            if source_file:
                st = os.stat(source)
                if C.MAX_FILE_SIZE_FOR_DIFF > 0 and st[stat.ST_SIZE] > C.MAX_FILE_SIZE_FOR_DIFF:
                    diff['src_larger'] = C.MAX_FILE_SIZE_FOR_DIFF
                else:
                    display.debug("Reading local copy of the file %s" % source)
                    try:
                        with open(source, 'rb') as src:
                            src_contents = src.read()
                    except Exception as e:
                        raise AnsibleError("Unexpected error while reading source (%s) for diff: %s " % (source, to_native(e)))

                    if b"\x00" in src_contents:
                        diff['src_binary'] = 1
                    else:
                        if content:
                            diff['after_header'] = destination
                        else:
                            diff['after_header'] = source
                        diff['after'] = to_text(src_contents)
            else:
                display.debug(u"source of file passed in")
                diff['after_header'] = u'dynamically generated'
                diff['after'] = source

        if self._task.no_log:
            if 'before' in diff:
                diff["before"] = u""
            if 'after' in diff:
                diff["after"] = u" [[ Diff output has been hidden because 'no_log: true' was specified for this result ]]\n"

        return diff