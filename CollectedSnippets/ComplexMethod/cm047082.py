def _prepare_build_dir(args, win32=False, move_addons=True):
    """Copy files to the build directory"""
    logging.info('Preparing build dir "%s"', args.build_dir)
    cmd = ['rsync', '-a', '--delete', '--exclude', '.git', '--exclude', '*.pyc', '--exclude', '*.pyo']
    if win32 is False:
        cmd += ['--exclude', 'setup/win32']

    run_cmd(cmd + ['%s/' % args.odoo_dir, args.build_dir])
    if not move_addons:
        return
    for addon_path in glob(os.path.join(args.build_dir, 'addons/*')):
        if args.blacklist is None or os.path.basename(addon_path) not in args.blacklist:
            try:
                shutil.move(addon_path, os.path.join(args.build_dir, 'odoo/addons'))
            except shutil.Error as e:
                logging.warning("Warning '%s' while moving addon '%s", e, addon_path)
                if addon_path.startswith(args.build_dir) and os.path.isdir(addon_path):
                    logging.info("Removing '{}'".format(addon_path))
                    try:
                        shutil.rmtree(addon_path)
                    except shutil.Error as rm_error:
                        logging.warning("Cannot remove '{}': {}".format(addon_path, rm_error))