def has_qbullet(reg, box, last_box, last_index, last_bull, bull_x0_list):
    section, last_section = box['text'], last_box['text']
    q_reg = r'(\w|\W)*?(?:？|\?|\n|$)+'
    full_reg = reg + q_reg
    has_bull = re.match(full_reg, section)
    index_str = None
    if has_bull:
        if 'x0' not in last_box:
            last_box['x0'] = box['x0']
        if 'top' not in last_box:
            last_box['top'] = box['top']
        if last_bull and box['x0'] - last_box['x0'] > 10:
            return None, last_index
        if not last_bull and box['x0'] >= last_box['x0'] and box['top'] - last_box['top'] < 20:
            return None, last_index
        avg_bull_x0 = 0
        if bull_x0_list:
            avg_bull_x0 = sum(bull_x0_list) / len(bull_x0_list)
        else:
            avg_bull_x0 = box['x0']
        if box['x0'] - avg_bull_x0 > 10:
            return None, last_index
        index_str = has_bull.group(1)
        index = index_int(index_str)
        if last_section[-1] == ':' or last_section[-1] == '：':
            return None, last_index
        if not last_index or index >= last_index:
            bull_x0_list.append(box['x0'])
            return has_bull, index
        if section[-1] == '?' or section[-1] == '？':
            bull_x0_list.append(box['x0'])
            return has_bull, index
        if box['layout_type'] == 'title':
            bull_x0_list.append(box['x0'])
            return has_bull, index
        pure_section = section.lstrip(re.match(reg, section).group()).lower()
        ask_reg = r'(what|when|where|how|why|which|who|whose|为什么|为啥|哪)'
        if re.match(ask_reg, pure_section):
            bull_x0_list.append(box['x0'])
            return has_bull, index
    return None, last_index