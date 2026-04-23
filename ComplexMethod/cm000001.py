def check_file_format(lines: List[str]) -> List[str]:

    err_msgs = []
    category_title_in_index = []

    alphabetical_err_msgs = check_alphabetical_order(lines)
    err_msgs.extend(alphabetical_err_msgs)

    num_in_category = min_entries_per_category + 1
    category = ''
    category_line = 0

    for line_num, line_content in enumerate(lines):

        category_title_match = category_title_in_index_re.match(line_content)
        if category_title_match:
            category_title_in_index.append(category_title_match.group(1))

        # check each category for the minimum number of entries
        if line_content.startswith(anchor):
            category_match = anchor_re.match(line_content)
            if category_match:
                if category_match.group(1) not in category_title_in_index:
                    err_msg = error_message(line_num, f'category header ({category_match.group(1)}) not added to Index section')
                    err_msgs.append(err_msg)
            else:
                err_msg = error_message(line_num, 'category header is not formatted correctly')
                err_msgs.append(err_msg)

            if num_in_category < min_entries_per_category:
                err_msg = error_message(category_line, f'{category} category does not have the minimum {min_entries_per_category} entries (only has {num_in_category})')
                err_msgs.append(err_msg)

            category = line_content.split(' ')[1]
            category_line = line_num
            num_in_category = 0
            continue

        # skips lines that we do not care about
        if not line_content.startswith('|') or line_content.startswith('|---'):
            continue

        num_in_category += 1
        segments = line_content.split('|')[1:-1]
        if len(segments) < num_segments:
            err_msg = error_message(line_num, f'entry does not have all the required columns (have {len(segments)}, need {num_segments})')
            err_msgs.append(err_msg)
            continue

        for segment in segments:
            # every line segment should start and end with exactly 1 space
            if len(segment) - len(segment.lstrip()) != 1 or len(segment) - len(segment.rstrip()) != 1:
                err_msg = error_message(line_num, 'each segment must start and end with exactly 1 space')
                err_msgs.append(err_msg)

        segments = [segment.strip() for segment in segments]
        entry_err_msgs = check_entry(line_num, segments)
        err_msgs.extend(entry_err_msgs)

    return err_msgs