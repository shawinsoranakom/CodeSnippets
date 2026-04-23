def test_cycle(args):
    """ Test full install/uninstall/reinstall cycle for all modules """
    with Registry(args.database).cursor() as cr:
        env = odoo.api.Environment(cr, odoo.api.SUPERUSER_ID, {})

        def valid(module):
            return not (
                module.name in BLACKLIST
                or module.name in INSTALL_BLACKLIST
                or module.name.startswith(IGNORE)
                or module.state in ('installed', 'uninstallable')
            )

        modules = env['ir.module.module'].search([]).filtered(valid)

        # order modules in topological order
        modules = modules.browse(topological_sort({
            module.id: module.dependencies_id.depend_id.ids
            for module in modules
        }))
        modules_todo = [(module.id, module.name) for module in modules]

    resume = args.resume_at
    skip = set(args.skip.split(',')) if args.skip else set()
    for module_id, module_name in modules_todo:
        if module_name == resume:
            resume = None

        if resume or module_name in skip:
            install(args.database, module_id, module_name)
        else:
            cycle(args.database, module_id, module_name)