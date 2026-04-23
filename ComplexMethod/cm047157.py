def run(self, cmdargs):
        parser = config.parser
        parser.prog = self.prog
        group = optparse.OptionGroup(parser, "Obfuscate Configuration")
        group.add_option('--pwd', dest="pwd", default=False, help="Cypher password")
        group.add_option('--fields', dest="fields", default=False, help="List of table.columns to obfuscate/unobfuscate: table1.column1,table2.column1,table2.column2")
        group.add_option('--exclude', dest="exclude", default=False, help="List of table.columns to exclude from obfuscate/unobfuscate: table1.column1,table2.column1,table2.column2")
        group.add_option('--file', dest="file", default=False, help="File containing the list of table.columns to obfuscate/unobfuscate")
        group.add_option('--unobfuscate', action='store_true', default=False)
        group.add_option('--allfields', action='store_true', default=False, help="Used in unobfuscate mode, try to unobfuscate all fields. Cannot be used in obfuscate mode. Slower than specifying fields.")
        group.add_option('--vacuum', action='store_true', default=False, help="Vacuum database after unobfuscating")
        group.add_option('--pertablecommit', action='store_true', default=False, help="Commit after each table instead of a big transaction")
        group.add_option(
            '-y', '--yes', dest="yes", action='store_true', default=False,
            help="Don't ask for manual confirmation. Use it carefully as the obfuscate method is not considered as safe to transfer anonymous datas to a third party.")

        parser.add_option_group(group)
        if not cmdargs:
            sys.exit(parser.print_help())

        try:
            opt = config.parse_config(cmdargs, setup_logging=True)
            if not opt.pwd:
                _logger.error("--pwd is required")
                sys.exit("ERROR: --pwd is required")
            if opt.allfields and not opt.unobfuscate:
                _logger.error("--allfields can only be used in unobfuscate mode")
                sys.exit("ERROR: --allfields can only be used in unobfuscate mode")
            if not opt.db_name:
                _logger.error('Obfuscate command needs a database name. Use "-d" argument')
                sys.exit('ERROR: Obfuscate command needs a database name. Use "-d" argument')
            if len(opt.db_name) > 1:
                _logger.error("-d/--database has multiple databases, please provide a single one")
                sys.exit("ERROR: -d/--database has multiple databases, please provide a single one")
            self.dbname = config['db_name'][0]
            self.registry = Registry(self.dbname)
            with self.registry.cursor() as cr:
                self.cr = cr
                self.begin()
                if self.check_pwd(opt.pwd):
                    fields = [
                            ('mail_tracking_value', 'old_value_char'),
                            ('mail_tracking_value', 'old_value_text'),
                            ('mail_tracking_value', 'new_value_char'),
                            ('mail_tracking_value', 'new_value_text'),
                            ('res_partner', 'name'),
                            ('res_partner', 'complete_name'),
                            ('res_partner', 'email'),
                            ('res_partner', 'phone'),
                            ('res_partner', 'mobile'),
                            ('res_partner', 'street'),
                            ('res_partner', 'street2'),
                            ('res_partner', 'city'),
                            ('res_partner', 'zip'),
                            ('res_partner', 'vat'),
                            ('res_partner', 'website'),
                            ('res_country', 'name'),
                            ('mail_message', 'subject'),
                            ('mail_message', 'email_from'),
                            ('mail_message', 'reply_to'),
                            ('mail_message', 'body'),
                            ('crm_lead', 'name'),
                            ('crm_lead', 'contact_name'),
                            ('crm_lead', 'partner_name'),
                            ('crm_lead', 'email_from'),
                            ('crm_lead', 'phone'),
                            ('crm_lead', 'mobile'),
                            ('crm_lead', 'website'),
                            ('crm_lead', 'description'),
                        ]

                    if opt.fields:
                        if not opt.allfields:
                            fields += [tuple(f.split('.')) for f in opt.fields.split(',')]
                        else:
                            _logger.error("--allfields option is set, ignoring --fields option")
                    if opt.file:
                        with open(opt.file, encoding='utf-8') as f:
                            fields += [tuple(l.strip().split('.')) for l in f]
                    if opt.exclude:
                        if not opt.allfields:
                            fields = [f for f in fields if f not in [tuple(f.split('.')) for f in opt.exclude.split(',')]]
                        else:
                            _logger.error("--allfields option is set, ignoring --exclude option")

                    if opt.allfields:
                        fields = self.get_all_fields()
                    else:
                        invalid_fields = [f for f in fields if not self.check_field(f[0], f[1])]
                        if invalid_fields:
                            _logger.error("Invalid fields: %s", ', '.join([f"{f[0]}.{f[1]}" for f in invalid_fields]))
                            fields = [f for f in fields if f not in invalid_fields]

                    if not opt.unobfuscate and not opt.yes:
                        self.confirm_not_secure()

                    _logger.info("Processing fields: %s", ', '.join([f"{f[0]}.{f[1]}" for f in fields]))
                    tables = defaultdict(set)

                    for t, f in fields:
                        if t[0:3] != 'ir_' and '.' not in t:
                            tables[t].add(f)

                    if opt.unobfuscate:
                        _logger.info("Unobfuscating datas")
                        for table in tables:
                            _logger.info("Unobfuscating table %s", table)
                            self.convert_table(table, tables[table], opt.pwd, opt.pertablecommit, True)

                        if opt.vacuum:
                            _logger.info("Vacuuming obfuscated tables")
                            for table in tables:
                                _logger.debug("Vacuuming table %s", table)
                                self.cr.execute(SQL("VACUUM FULL %s", SQL.identifier(table)))
                        self.clear_pwd()
                    else:
                        _logger.info("Obfuscating datas")
                        self.set_pwd(opt.pwd)
                        for table in tables:
                            _logger.info("Obfuscating table %s", table)
                            self.convert_table(table, tables[table], opt.pwd, opt.pertablecommit)

                    self.commit()
                else:
                    self.rollback()

        except Exception as e:  # noqa: BLE001
            sys.exit("ERROR: %s" % e)