def _format_act_list(self, act_list):
        role_groups = {}
        for act in traverse_obj(act_list, (..., {dict})):
            role = act.get('role')
            if role not in role_groups:
                role_groups[role] = []
            role_groups[role].append(act)

        formatted_roles = []
        for role, acts in role_groups.items():
            for i, act in enumerate(acts):
                res = f'【{role}】' if i == 0 and role is not None else ''
                if title := act.get('title'):
                    res += f'{title}…'
                formatted_roles.append(join_nonempty(res, act.get('name'), delim=''))
        return join_nonempty(*formatted_roles, delim='，')