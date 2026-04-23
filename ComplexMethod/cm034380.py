def present(module, dest, regexp, search_string, line, insertafter, insertbefore, create,
            backup, backrefs, firstmatch):

    diff = {'before': '',
            'after': '',
            'before_header': '%s (content)' % dest,
            'after_header': '%s (content)' % dest}

    encoding = module.params.get('encoding', None)
    b_dest = to_bytes(dest, errors='surrogate_or_strict')
    if not os.path.exists(b_dest):
        if not create:
            module.fail_json(rc=257, msg='Destination %s does not exist !' % dest)
        b_destpath = os.path.dirname(b_dest)
        if b_destpath and not os.path.exists(b_destpath) and not module.check_mode:
            try:
                os.makedirs(b_destpath)
            except Exception as e:
                module.fail_json(msg='Error creating %s (%s)' % (to_text(b_destpath), to_text(e)))

        lines = []
    else:
        with open(b_dest, 'r', encoding=encoding) as f:
            lines = f.readlines()

    if module._diff:
        diff['before'] = ''.join(lines)

    if regexp is not None:
        re_m = re.compile(regexp)

    if insertafter not in (None, 'BOF', 'EOF'):
        re_ins = re.compile(insertafter)
    elif insertbefore not in (None, 'BOF'):
        re_ins = re.compile(insertbefore)
    else:
        re_ins = None

    # index[0] is the line num where regexp has been found
    # index[1] is the line num where insertafter/insertbefore has been found
    index = [-1, -1]
    match = None
    exact_line_match = False

    # The module's doc says
    # "If regular expressions are passed to both regexp and
    # insertafter, insertafter is only honored if no match for regexp is found."
    # Therefore:
    # 1. regexp or search_string was found -> ignore insertafter, replace the founded line
    # 2. regexp or search_string was not found -> insert the line after 'insertafter' or 'insertbefore' line

    # Given the above:
    # 1. First check that there is no match for regexp:
    if regexp is not None:
        for lineno, cur_line in enumerate(lines):
            match_found = re_m.search(cur_line)
            if match_found:
                index[0] = lineno
                match = match_found
                if firstmatch:
                    break

    # 2. Second check that there is no match for search_string:
    if search_string is not None:
        for lineno, cur_line in enumerate(lines):
            match_found = search_string in cur_line
            if match_found:
                index[0] = lineno
                match = match_found
                if firstmatch:
                    break

    # 3. When no match found on the previous step,
    # parse for searching insertafter/insertbefore:
    if not match:
        for lineno, cur_line in enumerate(lines):
            if line == cur_line.rstrip('\r\n'):
                index[0] = lineno
                exact_line_match = True

            elif re_ins is not None and re_ins.search(cur_line):
                if insertafter:
                    # + 1 for the next line
                    index[1] = lineno + 1
                    if firstmatch:
                        break

                if insertbefore:
                    # index[1] for the previous line
                    index[1] = lineno
                    if firstmatch:
                        break

    msg = ''
    changed = False
    linesep = os.linesep
    # Exact line or Regexp matched a line in the file
    if index[0] != -1:
        if backrefs and match:
            new_line = match.expand(line)
        else:
            # Don't do backref expansion if not asked.
            new_line = line

        if not new_line.endswith(linesep):
            new_line += linesep

        # If no regexp or search_string was given and no line match is found anywhere in the file,
        # insert the line appropriately if using insertbefore or insertafter
        if (regexp, search_string, match) == (None, None, None) and not exact_line_match:

            # Insert lines
            if insertafter and insertafter != 'EOF':
                # Ensure there is a line separator after the found string
                # at the end of the file.
                if lines and not lines[-1][-1:] in ('\n', '\r'):
                    lines[-1] = lines[-1] + linesep

                # If the line to insert after is at the end of the file
                # use the appropriate index value.
                if len(lines) == index[1]:
                    if lines[index[1] - 1].rstrip('\r\n') != line:
                        lines.append(line + linesep)
                        msg = 'line added'
                        changed = True
                elif lines[index[1]].rstrip('\r\n') != line:
                    lines.insert(index[1], line + linesep)
                    msg = 'line added'
                    changed = True

            elif insertbefore and insertbefore != 'BOF':
                # If the line to insert before is at the beginning of the file
                # use the appropriate index value.
                if index[1] <= 0:
                    if lines[index[1]].rstrip('\r\n') != line:
                        lines.insert(index[1], line + linesep)
                        msg = 'line added'
                        changed = True

                elif lines[index[1] - 1].rstrip('\r\n') != line:
                    lines.insert(index[1], line + linesep)
                    msg = 'line added'
                    changed = True

        elif lines[index[0]] != new_line:
            lines[index[0]] = new_line
            msg = 'line replaced'
            changed = True

    elif backrefs:
        # Do absolutely nothing, since it's not safe generating the line
        # without the regexp matching to populate the backrefs.
        pass
    # Add it to the beginning of the file
    elif insertbefore == 'BOF' or insertafter == 'BOF':
        lines.insert(0, line + linesep)
        msg = 'line added'
        changed = True
    # Add it to the end of the file if requested or
    # if insertafter/insertbefore didn't match anything
    # (so default behaviour is to add at the end)
    elif insertafter == 'EOF' or index[1] == -1:

        # If the file is not empty then ensure there's a newline before the added line
        if lines and not lines[-1][-1:] in ('\n', '\r'):
            lines.append(linesep)

        lines.append(line + linesep)
        msg = 'line added'
        changed = True

    elif insertafter and index[1] != -1:

        # Don't insert the line if it already matches at the index.
        # If the line to insert after is at the end of the file use the appropriate index value.
        if len(lines) == index[1]:
            if lines[index[1] - 1].rstrip('\r\n') != line:
                lines.append(line + linesep)
                msg = 'line added'
                changed = True
        elif line != lines[index[1]].rstrip('\n\r'):
            lines.insert(index[1], line + linesep)
            msg = 'line added'
            changed = True

    # insert matched, but not the regexp or search_string
    else:
        lines.insert(index[1], line + linesep)
        msg = 'line added'
        changed = True

    if module._diff:
        diff['after'] = ''.join(lines)

    backupdest = ""
    if changed and not module.check_mode:
        if backup and os.path.exists(b_dest):
            backupdest = module.backup_local(dest)
        write_changes(module, lines, dest, encoding)

    if module.check_mode and not os.path.exists(b_dest):
        module.exit_json(changed=changed, msg=msg, backup=backupdest, diff=diff)

    attr_diff = {}
    msg, changed = check_file_attrs(module, changed, msg, attr_diff)

    attr_diff['before_header'] = '%s (file attributes)' % dest
    attr_diff['after_header'] = '%s (file attributes)' % dest

    difflist = [diff, attr_diff]
    module.exit_json(changed=changed, msg=msg, backup=backupdest, diff=difflist)