def cut_new(limit, get_token_fn, txt_tocut, must_break_at_empty_line, must_break_at_one_empty_line=False, break_anyway=False):
    """ 文本切分
    """
    res = []
    res_empty_line = []
    total_len = len(txt_tocut)
    fin_len = 0
    remain_txt_to_cut = txt_tocut
    remain_txt_to_cut_storage = ""
    # 为了加速计算，我们采样一个特殊的手段。当 remain_txt_to_cut > `_max` 时， 我们把 _max 后的文字转存至 remain_txt_to_cut_storage
    remain_txt_to_cut, remain_txt_to_cut_storage = maintain_storage(remain_txt_to_cut, remain_txt_to_cut_storage)
    empty=0

    while True:
        if get_token_fn(remain_txt_to_cut) <= limit:
            # 如果剩余文本的token数小于限制，那么就不用切了
            res.append(remain_txt_to_cut); fin_len+=len(remain_txt_to_cut)
            res_empty_line.append(empty)
            break
        else:
            # 如果剩余文本的token数大于限制，那么就切
            lines = remain_txt_to_cut.split('\n')

            # 估计一个切分点
            estimated_line_cut = limit / get_token_fn(remain_txt_to_cut) * len(lines)
            estimated_line_cut = int(estimated_line_cut)

            # 开始查找合适切分点的偏移（cnt）
            cnt = 0
            for cnt in reversed(range(estimated_line_cut)):
                if must_break_at_empty_line:
                    # 首先尝试用双空行（\n\n）作为切分点
                    if lines[cnt] != "":
                        continue
                if must_break_at_empty_line or must_break_at_one_empty_line:
                    empty=1
                prev = "\n".join(lines[:cnt])
                post = "\n".join(lines[cnt:])
                if get_token_fn(prev) < limit :
                    break
                    # empty=0
                if get_token_fn(prev)>limit:
                    if '.' not in prev or '。' not in prev:
                        # empty = 0
                        break

            # if cnt
            if cnt == 0:
                # 如果没有找到合适的切分点
                if break_anyway:
                    # 是否允许暴力切分
                    prev, post = force_breakdown(remain_txt_to_cut, limit, get_token_fn)
                    empty =0
                else:
                    # 不允许直接报错
                    raise RuntimeError(f"存在一行极长的文本！{remain_txt_to_cut}")

            # 追加列表
            res.append(prev); fin_len+=len(prev)
            res_empty_line.append(empty)
            # 准备下一次迭代
            remain_txt_to_cut = post
            remain_txt_to_cut, remain_txt_to_cut_storage = maintain_storage(remain_txt_to_cut, remain_txt_to_cut_storage)
            process = fin_len/total_len
            logger.info(f'正在文本切分 {int(process*100)}%')
            if len(remain_txt_to_cut.strip()) == 0:
                break
    return res,res_empty_line