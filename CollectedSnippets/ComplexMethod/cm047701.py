def _tag_menuitem(self, rec, parent=None):
        rec_id = rec.attrib["id"]
        self._test_xml_id(rec_id)

        # The parent attribute was specified, if non-empty determine its ID, otherwise
        # explicitly make a top-level menu
        values = {
            'parent_id': False,
            'active': nodeattr2bool(rec, 'active', default=True),
        }

        if rec.get('sequence'):
            values['sequence'] = int(rec.get('sequence'))

        if parent is not None:
            values['parent_id'] = parent
        elif rec.get('parent'):
            values['parent_id'] = self.id_get(rec.attrib['parent'])
        elif rec.get('web_icon'):
            values['web_icon'] = rec.attrib['web_icon']


        if rec.get('name'):
            values['name'] = rec.attrib['name']

        if rec.get('action'):
            a_action = rec.attrib['action']

            if '.' not in a_action:
                a_action = '%s.%s' % (self.module, a_action)
            act = self.env.ref(a_action).sudo()
            values['action'] = "%s,%d" % (act.type, act.id)

            if not values.get('name') and act.type.endswith(('act_window', 'wizard', 'url', 'client', 'server')) and act.name:
                values['name'] = act.name

        if not values.get('name'):
            values['name'] = rec_id or '?'

        from odoo.fields import Command  # noqa: PLC0415
        groups = []
        for group in rec.get('groups', '').split(','):
            if group.startswith('-'):
                group_id = self.id_get(group[1:])
                groups.append(Command.unlink(group_id))
            elif group:
                group_id = self.id_get(group)
                groups.append(Command.link(group_id))
        if groups:
            values['group_ids'] = groups


        data = {
            'xml_id': self.make_xml_id(rec_id),
            'values': values,
            'noupdate': self.noupdate,
        }
        menu = self.env['ir.ui.menu']._load_records([data], self.mode == 'update')
        for child in rec.iterchildren('menuitem'):
            self._tag_menuitem(child, parent=menu.id)