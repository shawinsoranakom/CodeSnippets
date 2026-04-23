def post_process(root):
    # 修复括号
    node = root
    while True:
        string = node.string
        if node.preserve:
            node = node.next
            if node is None:
                break
            continue

        def break_check(string):
            str_stack = [""]  # (lv, index)
            for i, c in enumerate(string):
                if c == "{":
                    str_stack.append("{")
                elif c == "}":
                    if len(str_stack) == 1:
                        logger.warning("fixing brace error")
                        return i
                    str_stack.pop(-1)
                else:
                    str_stack[-1] += c
            return -1

        bp = break_check(string)

        if bp == -1:
            pass
        elif bp == 0:
            node.string = string[:1]
            q = LinkedListNode(string[1:], False)
            q.next = node.next
            node.next = q
        else:
            node.string = string[:bp]
            q = LinkedListNode(string[bp:], False)
            q.next = node.next
            node.next = q

        node = node.next
        if node is None:
            break

    # 屏蔽空行和太短的句子
    node = root
    while True:
        if len(node.string.strip("\n").strip("")) == 0:
            node.preserve = True
        if len(node.string.strip("\n").strip("")) < 42:
            node.preserve = True
        node = node.next
        if node is None:
            break
    node = root
    while True:
        if node.next and node.preserve and node.next.preserve:
            node.string += node.next.string
            node.next = node.next.next
        node = node.next
        if node is None:
            break

    # 将前后断行符脱离
    node = root
    prev_node = None
    while True:
        if not node.preserve:
            lstriped_ = node.string.lstrip().lstrip("\n")
            if (
                (prev_node is not None)
                and (prev_node.preserve)
                and (len(lstriped_) != len(node.string))
            ):
                prev_node.string += node.string[: -len(lstriped_)]
                node.string = lstriped_
            rstriped_ = node.string.rstrip().rstrip("\n")
            if (
                (node.next is not None)
                and (node.next.preserve)
                and (len(rstriped_) != len(node.string))
            ):
                node.next.string = node.string[len(rstriped_) :] + node.next.string
                node.string = rstriped_
        # =-=-=
        prev_node = node
        node = node.next
        if node is None:
            break

    # 标注节点的行数范围
    node = root
    n_line = 0
    expansion = 2
    while True:
        n_l = node.string.count("\n")
        node.range = [n_line - expansion, n_line + n_l + expansion]  # 失败时，扭转的范围
        n_line = n_line + n_l
        node = node.next
        if node is None:
            break
    return root