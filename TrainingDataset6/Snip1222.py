def output(branch_name):
    if not branch_name:
        return ""
    output_str = u"error: pathspec '{}' did not match any file(s) known to git"
    return output_str.format(branch_name)