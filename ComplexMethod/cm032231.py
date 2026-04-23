def auto_context_clip_each_message(current, history):
    """
    clip_history 是被动触发的

    主动触发裁剪
    """
    context = history + [current]
    trigger_clip_token_len = get_conf('AUTO_CONTEXT_CLIP_TRIGGER_TOKEN_LEN')
    model_info = get_model_info()
    tokenizer = model_info['gpt-4']['tokenizer']
    # 只保留最近的128条记录，无论token长度，防止计算token时计算过长的时间
    max_round = get_conf('AUTO_CONTEXT_MAX_ROUND')
    char_len = sum([len(h) for h in context])
    if char_len < trigger_clip_token_len*2:
        # 不需要裁剪
        history = context[:-1]
        current = context[-1]
        return current, history
    if len(context) > max_round:
        context = context[-max_round:]
    # 计算各个历史记录的token长度
    context_token_num = [get_token_num(h, tokenizer) for h in context]
    context_token_num_old = copy.copy(context_token_num)
    total_token_num = total_token_num_old = sum(context_token_num)
    if total_token_num < trigger_clip_token_len:
        # 不需要裁剪
        history = context[:-1]
        current = context[-1]
        return current, history
    clip_token_len = trigger_clip_token_len * 0.85
    # 越长越先被裁，越靠后越先被裁
    max_clip_ratio: list[float] = get_conf('AUTO_CONTEXT_MAX_CLIP_RATIO')
    max_clip_ratio = list(reversed(max_clip_ratio))
    if len(context) > len(max_clip_ratio):
        # give up the oldest context
        context = context[-len(max_clip_ratio):]
        context_token_num = context_token_num[-len(max_clip_ratio):]
    if len(context) < len(max_clip_ratio):
        # match the length of two array
        max_clip_ratio = max_clip_ratio[-len(context):]

    # compute rank
    clip_prior_weight = [(token_num/clip_token_len + (len(context) - index)*0.1) for index, token_num in enumerate(context_token_num)]
    # print('clip_prior_weight', clip_prior_weight)
    # get sorted index of context_token_num, from largest to smallest
    sorted_index = sorted(range(len(context_token_num)), key=lambda k: clip_prior_weight[k], reverse=True)

    # pre compute space yield
    for index in sorted_index:
        print('index', index, f'current total {total_token_num}, target {clip_token_len}')
        if total_token_num < clip_token_len:
            # no need to clip
            break
        # clip room left
        clip_room_left = total_token_num - clip_token_len
        # get the clip ratio
        allowed_token_num_this_entry = max_clip_ratio[index] * clip_token_len
        if context_token_num[index] < allowed_token_num_this_entry:
            print('index', index, '[allowed] before', context_token_num[index], 'allowed', allowed_token_num_this_entry)
            continue

        token_to_clip = context_token_num[index] - allowed_token_num_this_entry
        if token_to_clip*0.85 > clip_room_left:
            print('index', index, '[careful clip] token_to_clip', token_to_clip, 'clip_room_left', clip_room_left)
            token_to_clip = clip_room_left

        token_percent_to_clip = token_to_clip / context_token_num[index]
        char_percent_to_clip = token_percent_to_clip
        text_this_entry = context[index]
        char_num_to_clip = int(len(text_this_entry) * char_percent_to_clip)
        if char_num_to_clip < 500:
            # 如果裁剪的字符数小于500，则不裁剪
            print('index', index, 'before', context_token_num[index], 'allowed', allowed_token_num_this_entry)
            continue
        char_num_to_clip += 200 # 稍微多加一点
        char_to_preseve = len(text_this_entry) - char_num_to_clip
        _half = int(char_to_preseve / 2)
        # 前半 + ... (content clipped because token overflows) ... + 后半
        text_this_entry_clip = text_this_entry[:_half] + \
                             " ... (content clipped because token overflows) ... " \
                             + text_this_entry[-_half:]
        context[index] = text_this_entry_clip
        post_clip_token_cnt = get_token_num(text_this_entry_clip, tokenizer)
        print('index', index, 'before', context_token_num[index], 'allowed', allowed_token_num_this_entry, 'after', post_clip_token_cnt)
        context_token_num[index] = post_clip_token_cnt
        total_token_num = sum(context_token_num)
    context_token_num_final = [get_token_num(h, tokenizer) for h in context]
    print('context_token_num_old', context_token_num_old)
    print('context_token_num_final', context_token_num_final)
    print('token change from', total_token_num_old, 'to', sum(context_token_num_final), 'target', clip_token_len)
    history = context[:-1]
    current = context[-1]
    return current, history