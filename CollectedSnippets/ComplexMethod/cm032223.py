def fix_dollar_sticking_bug(txt):
    """
    修复不标准的dollar公式符号的问题
    """
    txt_result = ""
    single_stack_height = 0
    double_stack_height = 0
    while True:
        while True:
            index = txt.find('$')

            if index == -1:
                txt_result += txt
                return txt_result

            if single_stack_height > 0:
                if txt[:(index+1)].find('\n') > 0 or txt[:(index+1)].find('<td>') > 0 or txt[:(index+1)].find('</td>') > 0:
                    logger.error('公式之中出现了异常 (Unexpect element in equation)')
                    single_stack_height = 0
                    txt_result += ' $'
                    continue

            if double_stack_height > 0:
                if txt[:(index+1)].find('\n\n') > 0:
                    logger.error('公式之中出现了异常 (Unexpect element in equation)')
                    double_stack_height = 0
                    txt_result += '$$'
                    continue

            is_double = (txt[index+1] == '$')
            if is_double:
                if single_stack_height != 0:
                    # add a padding
                    txt = txt[:(index+1)] + " " + txt[(index+1):]
                    continue
                if double_stack_height == 0:
                    double_stack_height = 1
                else:
                    double_stack_height = 0
                txt_result += txt[:(index+2)]
                txt = txt[(index+2):]
            else:
                if double_stack_height != 0:
                    # logger.info(txt[:(index)])
                    logger.info('发现异常嵌套公式')
                if single_stack_height == 0:
                    single_stack_height = 1
                else:
                    single_stack_height = 0
                    # logger.info(txt[:(index)])
                txt_result += txt[:(index+1)]
                txt = txt[(index+1):]
            break