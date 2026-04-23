def _check_str(result, func, cargs):
        res = check_string(result, func, cargs, offset=offset, str_result=str_result)
        if res and decoding:
            res = res.decode(decoding)
        return res