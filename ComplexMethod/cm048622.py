def _increase_rank(self, field: str, n: int = 1):
        assert field in ('customer_rank', 'supplier_rank')
        if not self:
            return
        postcommit = self.env.cr.postcommit
        data = postcommit.data.setdefault(f'account.res.partner.increase_rank.{field}', defaultdict(int))
        already_registered = bool(data)
        for record in self.sudo():
            # In case we alrady have a value, we will increase the rank in
            # postcommit to avoid serialization errors.  However, if the record
            # has a rank of 0, we increase it directly so that filtering on
            # partner_type is correctly set to customer or supplier.
            if record[field] and record.id:
                data[record.id] += n
            else:
                record[field] += n

        if already_registered or not data:
            return

        @postcommit.add
        def increase_partner_rank():
            try:
                with self.env.registry.cursor() as cr:
                    partners = (
                        self.env(cr=cr)[self._name]
                        .sudo().browse(data)
                        .with_context(prefetch_fields=False)
                    )
                    for partner in partners:
                        partner[field] += data[partner.id]
                    data.clear()
            except pgerrors.OperationalError:
                _logger.debug('Cannot update partner ranks.')