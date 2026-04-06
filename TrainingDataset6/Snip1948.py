def get_new_command(command):
    branch_name = first_0flag(command.script_parts)
    fixed_flag = branch_name.replace("0", "-")
    fixed_script = command.script.replace(branch_name, fixed_flag)
    if "A branch named '" in command.output and "' already exists." in command.output:
        delete_branch = u"git branch -D {}".format(branch_name)
        return shell.and_(delete_branch, fixed_script)
    return fixed_script