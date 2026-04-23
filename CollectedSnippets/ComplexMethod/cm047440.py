def is_whitelisted_argument(arg):
    if isinstance(arg, (astroid.Name, astroid.Attribute)):
        return True
    if isinstance(arg, astroid.Subscript):  # ex: errors[0]
        return True
    if isinstance(arg, astroid.Call):  # Assumption: any call inside Error call would return a translated string.
        return True
    if isinstance(arg, astroid.IfExp):  # ex: UserError(_("string_1") if condition else _("string_2"))
        return is_whitelisted_argument(arg.body) and is_whitelisted_argument(arg.orelse)
    if isinstance(arg, astroid.BoolOp):  # ex: UserError(_("string_1") and errors[0] or errors_list.get("msg"))
        return all(is_whitelisted_argument(node) for node in arg.values)
    if isinstance(arg, astroid.BinOp):  # ex: UserError(a + b)
        return is_whitelisted_argument(arg.right) or is_whitelisted_argument(arg.left)
    return False