def _initialize_db(db_name, demo, lang, user_password, login='admin', country_code=None, phone=None):
    try:
        odoo.tools.config['load_language'] = lang

        registry = odoo.modules.registry.Registry.new(db_name, update_module=True, new_db_demo=demo)

        with closing(registry.cursor()) as cr:
            env = odoo.api.Environment(cr, odoo.api.SUPERUSER_ID, {})

            if lang:
                modules = env['ir.module.module'].search([('state', '=', 'installed')])
                modules._update_translations(lang)

            if country_code:
                country = env['res.country'].search([('code', 'ilike', country_code)])[0]
                env['res.company'].browse(1).write({'country_id': country_code and country.id, 'currency_id': country_code and country.currency_id.id})
                if len(country_timezones.get(country_code, [])) == 1:
                    users = env['res.users'].search([])
                    users.write({'tz': country_timezones[country_code][0]})
            if phone:
                env['res.company'].browse(1).write({'phone': phone})
            if '@' in login:
                env['res.company'].browse(1).write({'email': login})

            # update admin's password and lang and login
            values = {'password': user_password, 'lang': lang}
            if login:
                values['login'] = login
                emails = odoo.tools.email_split(login)
                if emails:
                    values['email'] = emails[0]
            env.ref('base.user_admin').write(values)

            cr.commit()
    except Exception as e:
        _logger.exception('CREATE DATABASE failed:')