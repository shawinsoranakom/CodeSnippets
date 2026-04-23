def check_version_upgrades(local_branch, db_branch):
    """
    Check if the iot is < 19.1 and upgrading to >= saas-19.1
    If so and current python version is less than 3.12, run the scripts
    located in upgrade_scripts/ to upgrade the python version
    :param local_branch: The local git branch (Ex: "19.0" / "17.0-hw-drivers-compatibility-with-trixie-yaso")
    :param db_branch: The git branch of the connected Odoo database (Ex: "saas-19.1" / "master" etc.)
    """
    try:
        # 1. Check if the upgrade script needs to be ran
        # Needed if local branch is < 19.1 and db branch is >= 19.1 + python version < 3.12
        _logger.info("Checking for version upgrades for local branch %s / db_branch %s", local_branch, db_branch)
        version_db = db_branch[-4:] if db_branch != 'master' else db_branch  # master is currently always >= 19.1
        version_local = local_branch[-4:] if local_branch != 'master' else local_branch
        local_python_version = tuple(int(x) for x in platform.python_version_tuple()[:2])
        if version_local >= '19.1' or version_db < '19.1' or local_python_version >= (3, 12):
            _logger.info("Ignoring unnecessary upgrade for local branch %s / db_branch %s with python version %s", local_branch, db_branch, local_python_version)
            return

        _logger.warning("Updating to Debian Trixie for >= 19.1")
        subprocess.run(
            ['/home/pi/odoo/addons/iot_drivers/tools/upgrade_scripts/upgrade_trixie/upgrade_trixie.sh'], check=True,
        )
    except subprocess.CalledProcessError:
        _logger.exception("Failed to upgrade to debian Trixie. Check /home/pi/upgrade.log file for more details")