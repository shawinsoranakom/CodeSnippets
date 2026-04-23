def get_action_triples(env, path, *, start_pos=0):
    """
    Extract the triples (active_id, action, record_id) from a "/odoo"-like path.

    >>> env = ...
    >>> list(get_action_triples(env, "/all-tasks/5/project.project/1/tasks"))
    [
        # active_id, action,                     record_id
        ( None,      ir.actions.act_window(...), 5         ), # all-tasks
        ( 5,         ir.actions.act_window(...), 1         ), # project.project
        ( 1,         ir.actions.act_window(...), None      ), # tasks
    ]
    """
    parts = collections.deque(path.strip('/').split('/'))
    active_id = None
    record_id = None

    while parts:
        if not parts:
            e = "expected action at word {} but found nothing"
            raise ValueError(e.format(path.count('/') + start_pos))
        action_name = parts.popleft()
        action = get_action(env, action_name)
        if not action:
            e = f"expected action at word {{}} but found “{action_name}”"
            raise ValueError(e.format(path.count('/') - len(parts) + start_pos))

        record_id = None
        if parts:
            if parts[0] == 'new':
                parts.popleft()
                record_id = None
            elif parts[0].isdigit():
                record_id = int(parts.popleft())

        yield (active_id, action, record_id)

        if len(parts) > 1 and parts[0].isdigit():  # new active id
            active_id = int(parts.popleft())
        elif record_id:
            active_id = record_id