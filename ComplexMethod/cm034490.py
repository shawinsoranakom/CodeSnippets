def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True, aliases=['pkg']),
            question=dict(type='str', aliases=['selection', 'setting']),
            vtype=dict(type='str', choices=['boolean', 'error', 'multiselect', 'note', 'password', 'seen', 'select', 'string', 'text', 'title']),
            value=dict(type='raw', aliases=['answer']),
            unseen=dict(type='bool', default=False),
        ),
        required_together=(['question', 'vtype', 'value'],),
        supports_check_mode=True,
    )

    # TODO: enable passing array of options and/or debconf file from get-selections dump
    pkg = module.params["name"]
    question = module.params["question"]
    vtype = module.params["vtype"]
    value = module.params["value"]
    unseen = module.params["unseen"]

    prev = get_selections(module, pkg)

    changed = False
    msg = ""

    if question is not None:
        if vtype is None or value is None:
            module.fail_json(msg="when supplying a question you must supply a valid vtype and value")

        # ensure we compare booleans supplied to the way debconf sees them (true/false strings)
        if vtype == 'boolean':
            value = to_text(value).lower()

        # if question doesn't exist, value cannot match
        if question not in prev:
            changed = True
        else:
            existing = prev[question]

            if vtype == 'boolean':
                existing = to_text(prev[question]).lower()
            elif vtype == 'password':
                existing = get_password_value(module, pkg, question, vtype)
            elif vtype == 'multiselect' and isinstance(value, list):
                try:
                    value = sorted(value)
                except TypeError as exc:
                    module.fail_json(msg="Invalid value provided for 'multiselect': %s" % to_native(exc))
                existing = sorted([i.strip() for i in existing.split(",")])

            if value != existing:
                changed = True

    if changed:
        if not module.check_mode:
            if vtype == 'multiselect' and isinstance(value, list):
                try:
                    value = ", ".join(value)
                except TypeError as exc:
                    module.fail_json(msg="Invalid value provided for 'multiselect': %s" % to_native(exc))
            rc, msg, e = set_selection(module, pkg, question, vtype, value, unseen)
            if rc:
                module.fail_json(msg=e)

        curr = {question: value}
        if question in prev:
            prev = {question: prev[question]}
        else:
            prev[question] = ''

        diff_dict = {}
        if module._diff:
            after = prev.copy()
            after.update(curr)
            diff_dict = {'before': prev, 'after': after}

        module.exit_json(changed=changed, msg=msg, current=curr, previous=prev, diff=diff_dict)

    module.exit_json(changed=changed, msg=msg, current=prev)