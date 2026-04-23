def _exec_action(action, datas, env):
        # taken from client/modules/action/main.py:84 _exec_action()
        if isinstance(action, bool) or 'type' not in action:
            return
        # Updating the context : Adding the context of action in order to use it on Views called from buttons
        context = dict(env.context)
        if datas.get('id',False):
            context.update( {'active_id': datas.get('id',False), 'active_ids': datas.get('ids',[]), 'active_model': datas.get('model',False)})
        context1 = action.get('context', {})
        if isinstance(context1, str):
            context1 = safe_eval(context1, dict(context))
        context.update(context1)
        env = env(context=context)
        if action['type'] in ['ir.actions.act_window', 'ir.actions.submenu']:
            for key in ('res_id', 'res_model', 'view_mode',
                        'limit', 'search_view_id'):
                datas[key] = action.get(key, datas.get(key, None))

            view_id = False
            view_type = None
            if action.get('views', []):
                if isinstance(action['views'],list):
                    view_id, view_type = action['views'][0]
                    datas['view_mode']= view_type
                else:
                    if action.get('view_id', False):
                        view_id = action['view_id'][0]
            elif action.get('view_id', False):
                view_id = action['view_id'][0]

            if view_type is None:
                if view_id:
                    view_type = env['ir.ui.view'].browse(view_id).type
                else:
                    view_type = action['view_mode'].split(',')[0]

            assert datas['res_model'], "Cannot use the view without a model"
            # Here, we have a view that we need to emulate
            log_test("will emulate a %s view: %s#%s",
                        view_type, datas['res_model'], view_id or '?')

            model = env[datas['res_model']]
            view_res = model.get_view(view_id, view_type)
            assert view_res and view_res.get('arch'), "Did not return any arch for the view"
            view_data = {}
            arch = etree.fromstring(view_res['arch'])
            fields = [el.get('name') for el in arch.xpath('//field[not(ancestor::field)]')]
            if fields:
                view_data = model.default_get(fields)
            if datas.get('form'):
                view_data.update(datas.get('form'))
            if wiz_data:
                view_data.update(wiz_data)
            _logger.debug("View data is: %r", view_data)

            for fk in fields:
                # Default fields returns list of int, while at create()
                # we need to send a [(6,0,[int,..])]
                if model._fields[fk].type in ('one2many', 'many2many') \
                        and view_data.get(fk, False) \
                        and isinstance(view_data[fk], list) \
                        and not isinstance(view_data[fk][0], tuple) :
                    view_data[fk] = [(6, 0, view_data[fk])]

            action_name = action.get('name')
            try:
                from xml.dom import minidom
                cancel_found = False
                buttons = []
                dom_doc = minidom.parseString(view_res['arch'])
                if not action_name:
                    action_name = dom_doc.documentElement.getAttribute('name')

                for button in dom_doc.getElementsByTagName('button'):
                    button_weight = 0
                    if button.getAttribute('special') == 'cancel':
                        cancel_found = True
                        continue
                    if button.getAttribute('icon') == 'fa-times-circle':
                        cancel_found = True
                        continue
                    if button.getAttribute('default_focus') == '1':
                        button_weight += 20
                    if button.getAttribute('string') in wiz_buttons:
                        button_weight += 30
                    elif button.getAttribute('icon') in wiz_buttons:
                        button_weight += 10
                    string = button.getAttribute('string') or '?%s' % len(buttons)

                    buttons.append({
                        'name': button.getAttribute('name'),
                        'string': string,
                        'type': button.getAttribute('type'),
                        'weight': button_weight,
                    })
            except Exception as e:
                _logger.warning("Cannot resolve the view arch and locate the buttons!", exc_info=True)
                raise AssertionError(e.args[0])

            if not datas['res_id']:
                # it is probably an orm_memory object, we need to create
                # an instance
                datas['res_id'] = env[datas['res_model']].create(view_data).id

            if not buttons:
                raise AssertionError("view form doesn't have any buttons to press!")

            buttons.sort(key=lambda b: b['weight'])
            _logger.debug('Buttons are: %s', ', '.join([ '%s: %d' % (b['string'], b['weight']) for b in buttons]))

            res = None
            while buttons and not res:
                b = buttons.pop()
                log_test("in the \"%s\" form, I will press the \"%s\" button.", action_name, b['string'])
                if not b['type']:
                    log_test("the \"%s\" button has no type, cannot use it", b['string'])
                    continue
                if b['type'] == 'object':
                    #there we are! press the button!
                    rec = env[datas['res_model']].browse(datas['res_id'])
                    func = getattr(rec, b['name'], None)
                    if not func:
                        _logger.error("The %s model doesn't have a %s attribute!", datas['res_model'], b['name'])
                        continue
                    res = func()
                    break
                else:
                    _logger.warning("in the \"%s\" form, the \"%s\" button has unknown type %s",
                        action_name, b['string'], b['type'])
            return res

        elif action['type']=='ir.actions.report':
            if 'window' in datas:
                del datas['window']
            if not datas:
                datas = action.get('datas')
                if not datas:
                    datas = action.get('data')
            datas = datas.copy()
            ids = datas.get('ids')
            if 'ids' in datas:
                del datas['ids']
            res = try_report(cr, uid, action['report_name'], ids, datas, context, our_module=our_module)
            return res
        else:
            raise Exception("Cannot handle action of type %s" % act_model)