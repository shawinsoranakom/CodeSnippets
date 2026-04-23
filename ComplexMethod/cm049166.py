def _get_so_mapping_from_project(self):
        """ Get the mapping of move.line with the sale.order record on which its analytic entries should be reinvoiced.
            A sale.order matches a move.line if the sale.order's project contains all the same analytic accounts
            as the ones in the distribution of the move.line.
            :return a dict where key is the move line id, and value is sale.order record (or None).
        """
        mapping = {}
        projects = self.env['project.project'].search(domain=self._get_so_mapping_domain())
        orders_per_project = dict(self.env['sale.order']._read_group(
            domain=[('project_id', 'in', projects.ids)],
            groupby=['project_id'],
            aggregates=['id:recordset']
        ))
        project_per_accounts = {
            next(iter(project._get_analytic_distribution())): project
            for project in projects
        }

        for move_line in self:
            analytic_distribution = move_line.analytic_distribution
            if not analytic_distribution:
                continue

            for accounts in analytic_distribution:
                project = project_per_accounts.get(accounts)
            if not project:
                continue

            orders = orders_per_project.get(project)
            if not orders:
                continue
            orders = orders.sorted('create_date')
            in_sale_state_orders = orders.filtered(lambda s: s.state == 'sale')

            mapping[move_line.id] = in_sale_state_orders[0] if in_sale_state_orders else orders[0]

        # map the move line index with the SO on which it needs to be reinvoiced. May be empty if no SO found
        return mapping