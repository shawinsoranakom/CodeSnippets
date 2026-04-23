def list_db_incompatible(databases):
    """"Check a list of databases if they are compatible with this version of Odoo

        :param databases: A list of existing Postgresql databases
        :return: A list of databases that are incompatible
    """
    incompatible_databases = []
    server_version = '.'.join(str(v) for v in version_info[:2])
    for database_name in databases:
        with closing(db_connect(database_name).cursor()) as cr:
            if odoo.tools.sql.table_exists(cr, 'ir_module_module'):
                cr.execute("SELECT latest_version FROM ir_module_module WHERE name=%s", ('base',))
                base_version = cr.fetchone()
                if not base_version or not base_version[0]:
                    incompatible_databases.append(database_name)
                else:
                    # e.g. 10.saas~15
                    local_version = '.'.join(base_version[0].split('.')[:2])
                    if local_version != server_version:
                        incompatible_databases.append(database_name)
            else:
                incompatible_databases.append(database_name)
    for database_name in incompatible_databases:
        # release connection
        odoo.sql_db.close_db(database_name)
    return incompatible_databases