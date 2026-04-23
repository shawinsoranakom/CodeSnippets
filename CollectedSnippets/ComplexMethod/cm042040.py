def repair_required_key_pair_missing(output: str, req_key: str = "[/CONTENT]") -> str:
    """
    implement the req_key pair in the begin or end of the content
        req_key format
            1. `[req_key]`, and its pair `[/req_key]`
            2. `[/req_key]`, and its pair `[req_key]`
    """
    sc = "/"  # special char
    if req_key.startswith("[") and req_key.endswith("]"):
        if sc in req_key:
            left_key = req_key.replace(sc, "")  # `[/req_key]` -> `[req_key]`
            right_key = req_key
        else:
            left_key = req_key
            right_key = f"{req_key[0]}{sc}{req_key[1:]}"  # `[req_key]` -> `[/req_key]`

        if left_key not in output:
            output = left_key + "\n" + output
        if right_key not in output:

            def judge_potential_json(routput: str, left_key: str) -> Union[str, None]:
                ridx = routput.rfind(left_key)
                if ridx < 0:
                    return None
                sub_output = routput[ridx:]
                idx1 = sub_output.rfind("}")
                idx2 = sub_output.rindex("]")
                idx = idx1 if idx1 >= idx2 else idx2
                sub_output = sub_output[: idx + 1]
                return sub_output

            if output.strip().endswith("}") or (output.strip().endswith("]") and not output.strip().endswith(left_key)):
                # # avoid [req_key]xx[req_key] case to append [/req_key]
                output = output + "\n" + right_key
            elif judge_potential_json(output, left_key) and (not output.strip().endswith(left_key)):
                sub_content = judge_potential_json(output, left_key)
                output = sub_content + "\n" + right_key

    return output