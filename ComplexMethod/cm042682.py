def run(self, args: list[str], opts: argparse.Namespace) -> None:
        assert self.settings is not None
        if opts.list:
            self._list_templates()
            return
        if opts.dump:
            template_file = self._find_template(opts.dump)
            if template_file:
                print(template_file.read_text(encoding="utf-8"))
            return
        if len(args) != 2:
            raise UsageError

        name, url = args[0:2]
        url = verify_url_scheme(url)
        module = sanitize_module_name(name)

        if self.settings.get("BOT_NAME") == module:
            print("Cannot create a spider with the same name as your project")
            return

        if not opts.force and self._spider_exists(name):
            return

        template_file = self._find_template(opts.template)
        if template_file:
            self._genspider(module, name, url, opts.template, template_file)
            if opts.edit:
                self.exitcode = os.system(f'scrapy edit "{name}"')