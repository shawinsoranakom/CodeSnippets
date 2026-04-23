def initialize_sys_path() -> None:
    """
    Setup the addons path ``odoo.addons.__path__`` with various defaults
    and explicit directories.
    """
    for path in (
        # tools.config.addons_base_dir,  # already present
        tools.config.addons_data_dir,
        *tools.config['addons_path'],
        tools.config.addons_community_dir,
    ):
        if os.access(path, os.R_OK) and path not in odoo.addons.__path__:
            odoo.addons.__path__.append(path)

    # hook odoo.upgrade on upgrade-path
    legacy_upgrade_path = os.path.join(tools.config.addons_base_dir, 'base/maintenance/migrations')
    for up in tools.config['upgrade_path'] or [legacy_upgrade_path]:
        if up not in odoo.upgrade.__path__:
            odoo.upgrade.__path__.append(up)

    # create decrecated module alias from odoo.addons.base.maintenance.migrations to odoo.upgrade
    spec = importlib.machinery.ModuleSpec("odoo.addons.base.maintenance", None, is_package=True)
    maintenance_pkg = importlib.util.module_from_spec(spec)
    maintenance_pkg.migrations = odoo.upgrade  # type: ignore
    sys.modules["odoo.addons.base.maintenance"] = maintenance_pkg
    sys.modules["odoo.addons.base.maintenance.migrations"] = odoo.upgrade

    # hook for upgrades and namespace freeze
    if not getattr(initialize_sys_path, 'called', False):  # only initialize once
        odoo.addons.__path__._path_finder = lambda *a: None  # prevent path invalidation
        odoo.upgrade.__path__._path_finder = lambda *a: None  # prevent path invalidation
        sys.meta_path.insert(0, UpgradeHook())
        initialize_sys_path.called = True