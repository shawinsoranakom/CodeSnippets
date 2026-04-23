def _parse_partner_to(cls, partner_to):
        try:
            partner_to = literal_eval(partner_to or '[]')
        except (ValueError, SyntaxError):
            partner_to = partner_to.split(',')
        if not isinstance(partner_to, (list, tuple)):
            partner_to = [partner_to]
        return [
            int(pid.strip()) if isinstance(pid, str) else int(pid) for pid in partner_to
            if (isinstance(pid, str) and pid.strip().isdigit()) or (pid and not isinstance(pid, str))
        ]