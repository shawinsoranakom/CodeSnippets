def initialize(cr: Cursor) -> None:
    """ Initialize a database with for the ORM.

    This executes base/data/base_data.sql, creates the ir_module_categories
    (taken from each module descriptor file), and creates the ir_module_module
    and ir_model_data entries.

    """
    try:
        f = odoo.tools.misc.file_path('base/data/base_data.sql')
    except FileNotFoundError:
        m = "File not found: 'base.sql' (provided by module 'base')."
        _logger.critical(m)
        raise OSError(m)

    with odoo.tools.misc.file_open(f) as base_sql_file:
        cr.execute(base_sql_file.read())  # pylint: disable=sql-injection

    for info in odoo.modules.Manifest.all_addon_manifests():
        module_name = info.name
        categories = info['category'].split('/')
        category_id = create_categories(cr, categories)

        if info['installable']:
            state = 'uninstalled'
        else:
            state = 'uninstallable'

        cr.execute('INSERT INTO ir_module_module \
                (author, website, name, shortdesc, description, \
                    category_id, auto_install, state, web, license, application, icon, sequence, summary) \
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id', (
            info['author'],
            info['website'], module_name, Json({'en_US': info['name']}),
            Json({'en_US': info['description']}), category_id,
            info['auto_install'] is not False, state,
            info['web'],
            info['license'],
            info['application'], info['icon'],
            info['sequence'], Json({'en_US': info['summary']})))
        row = cr.fetchone()
        assert row is not None  # for typing
        module_id = row[0]
        cr.execute(
            'INSERT INTO ir_model_data'
            '(name,model,module, res_id, noupdate) VALUES (%s,%s,%s,%s,%s)',
            ('module_' + module_name, 'ir.module.module', 'base', module_id, True),
        )
        dependencies = info['depends']
        for d in dependencies:
            cr.execute(
                'INSERT INTO ir_module_module_dependency (module_id, name, auto_install_required)'
                ' VALUES (%s, %s, %s)',
                (module_id, d, d in (info['auto_install'] or ()))
            )

    from odoo.tools import config  # noqa: PLC0415
    if config.get('skip_auto_install'):
        # even if skip_auto_install is enabled we still want to have base
        cr.execute("""UPDATE ir_module_module SET state='to install' WHERE name = 'base'""")
        return

    # Install recursively all auto-installing modules
    while True:
        # this selects all the auto_install modules whose auto_install_required
        # deps are marked as to install
        cr.execute("""
        SELECT m.name FROM ir_module_module m
        WHERE m.auto_install
        AND state not in ('to install', 'uninstallable')
        AND NOT EXISTS (
            SELECT 1 FROM ir_module_module_dependency d
            JOIN ir_module_module mdep ON (d.name = mdep.name)
            WHERE d.module_id = m.id
              AND d.auto_install_required
              AND mdep.state != 'to install'
        )""")
        to_auto_install = [x[0] for x in cr.fetchall()]
        # however if the module has non-required deps we need to install
        # those, so merge-in the modules which have a dependen*t* which is
        # *either* to_install or in to_auto_install and merge it in?
        cr.execute("""
        SELECT d.name FROM ir_module_module_dependency d
        JOIN ir_module_module m ON (d.module_id = m.id)
        JOIN ir_module_module mdep ON (d.name = mdep.name)
        WHERE (m.state = 'to install' OR m.name = any(%s))
            -- don't re-mark marked modules
        AND NOT (mdep.state = 'to install' OR mdep.name = any(%s))
        """, [to_auto_install, to_auto_install])
        to_auto_install.extend(x[0] for x in cr.fetchall())

        if not to_auto_install:
            break
        cr.execute("""UPDATE ir_module_module SET state='to install' WHERE name in %s""", (tuple(to_auto_install),))