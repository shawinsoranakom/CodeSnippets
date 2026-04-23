def run(self):

        super(InventoryCLI, self).run()

        # Initialize needed objects
        self.loader, self.inventory, self.vm = self._play_prereqs()

        results = None
        if context.CLIARGS['host']:
            hosts = self.inventory.get_hosts(context.CLIARGS['host'])
            if len(hosts) != 1:
                raise AnsibleOptionsError("You must pass a single valid host to --host parameter")

            myvars = self._get_host_variables(host=hosts[0])

            # FIXME: should we template first?
            results = self.dump(myvars)

        else:
            if context.CLIARGS['subset']:
                # not doing single host, set limit in general if given
                self.inventory.subset(context.CLIARGS['subset'])

            if context.CLIARGS['graph']:
                results = self.inventory_graph()
            elif context.CLIARGS['list']:
                top = self._get_group('all')
                if context.CLIARGS['yaml']:
                    results = self.yaml_inventory(top)
                elif context.CLIARGS['toml']:
                    results = self.toml_inventory(top)
                else:
                    results = self.json_inventory(top)
                results = self.dump(results)

        if results:
            outfile = context.CLIARGS['output_file']
            if outfile is None:
                # FIXME: pager?
                display.display(results)
            else:
                try:
                    with open(to_bytes(outfile), 'wb') as f:
                        f.write(to_bytes(results))
                except OSError as ex:
                    raise AnsibleError(f'Unable to write to destination file {outfile!r}.') from ex
            sys.exit(0)

        sys.exit(1)