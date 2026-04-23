def fix_code_segment_indent(txt):
    lines = []
    change_any = False
    txt_tmp = txt
    while True:
        re_match_obj = FENCED_BLOCK_RE.search(txt_tmp)
        if not re_match_obj:
            break
        if len(lines) == 0:
            lines = txt.split("\n")

        # 清空 txt_tmp 对应的位置方便下次搜索
        start_pos, end_pos = re_match_obj.regs[0]
        txt_tmp = txt_tmp[:start_pos] + " " * (end_pos - start_pos) + txt_tmp[end_pos:]
        line_start, line_end = get_line_range(re_match_obj, txt)

        # 获取公共缩进
        shared_indent_cnt = 1e5
        for i in range(line_start, line_end):
            stripped_string = lines[i].lstrip()
            num_spaces = len(lines[i]) - len(stripped_string)
            if num_spaces < shared_indent_cnt:
                shared_indent_cnt = num_spaces

        # 修复缩进
        if (shared_indent_cnt < 1e5) and (shared_indent_cnt % 4) == 3:
            num_spaces_should_be = math.ceil(shared_indent_cnt / 4) * 4
            for i in range(line_start, line_end):
                add_n = num_spaces_should_be - shared_indent_cnt
                lines[i] = " " * add_n + lines[i]
            if not change_any:  # 遇到第一个
                change_any = True

    if change_any:
        return "\n".join(lines)
    else:
        return txt