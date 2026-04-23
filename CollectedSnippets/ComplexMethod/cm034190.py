def _play_ds(self, pattern, async_val, poll):
        check_raw = context.CLIARGS['module_name'] in C.MODULE_REQUIRE_ARGS

        module_args_raw = context.CLIARGS['module_args']
        module_args = None
        if module_args_raw and module_args_raw.startswith('{') and module_args_raw.endswith('}'):
            try:
                module_args = json.loads(module_args_raw, cls=_legacy.Decoder)
            except AnsibleParserError:
                pass

        if not module_args:
            module_args = parse_kv(module_args_raw, check_raw=check_raw)

        mytask = dict(
            action=context.CLIARGS['module_name'],
            args=module_args,
            timeout=context.CLIARGS['task_timeout'],
        )

        mytask = Origin(description=f'<adhoc {context.CLIARGS["module_name"]!r} task>').tag(mytask)

        # avoid adding to tasks that don't support it, unless set, then give user an error
        if context.CLIARGS['module_name'] not in C._ACTION_ALL_INCLUDE_ROLE_TASKS and any(frozenset((async_val, poll))):
            mytask['async_val'] = async_val
            mytask['poll'] = poll

        return dict(
            name="Ansible Ad-Hoc",
            hosts=pattern,
            gather_facts='no',
            tasks=[mytask])