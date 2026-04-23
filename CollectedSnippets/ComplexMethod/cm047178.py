def restore_db(db, dump_file, copy=False, neutralize_database=False):
    assert isinstance(db, str)
    if exp_db_exist(db):
        _logger.warning('RESTORE DB: %s already exists', db)
        raise Exception("Database already exists")

    _logger.info('RESTORING DB: %s', db)
    _create_empty_database(db)

    filestore_path = None
    with tempfile.TemporaryDirectory() as dump_dir:
        if zipfile.is_zipfile(dump_file):
            # v8 format
            with zipfile.ZipFile(dump_file, 'r') as z:
                # only extract known members!
                filestore = [m for m in z.namelist() if m.startswith('filestore/')]
                z.extractall(dump_dir, ['dump.sql'] + filestore)

                if filestore:
                    filestore_path = os.path.join(dump_dir, 'filestore')

            pg_cmd = 'psql'
            pg_args = ['-q', '-f', os.path.join(dump_dir, 'dump.sql')]

        else:
            # <= 7.0 format (raw pg_dump output)
            pg_cmd = 'pg_restore'
            pg_args = ['--no-owner', dump_file]

        r = subprocess.run(
            [find_pg_tool(pg_cmd), '--dbname=' + db, *pg_args],
            env=exec_pg_environ(),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
        )
        if r.returncode != 0:
            raise Exception("Couldn't restore database")

        registry = odoo.modules.registry.Registry.new(db)
        with registry.cursor() as cr:
            env = odoo.api.Environment(cr, odoo.api.SUPERUSER_ID, {})
            if copy:
                # if it's a copy of a database, force generation of a new dbuuid
                env['ir.config_parameter'].init(force=True)
            if neutralize_database:
                odoo.modules.neutralize.neutralize_database(cr)

            if filestore_path:
                filestore_dest = env['ir.attachment']._filestore()
                shutil.move(filestore_path, filestore_dest)

    _logger.info('RESTORE DB: %s', db)