def _procure_orderpoint_confirm(self, use_new_cursor=False, company_id=None, raise_user_error=True):
        """ Create procurements based on orderpoints.
        :param bool use_new_cursor: if set, use a dedicated cursor and auto-commit after processing
            1000 orderpoints.
            This is appropriate for batch jobs only.
        """
        self = self.with_company(company_id)

        for orderpoints_batch_ids in split_every(1000, self.ids):
            if use_new_cursor:
                assert isinstance(self.env.cr, BaseCursor)
                cr = Registry(self.env.cr.dbname).cursor()
                self = self.with_env(self.env(cr=cr))
            try:
                orderpoints_batch = self.env['stock.warehouse.orderpoint'].browse(orderpoints_batch_ids)
                all_orderpoints_exceptions = []
                while orderpoints_batch:
                    procurements = []
                    for orderpoint in orderpoints_batch:
                        origins = orderpoint.env.context.get('origins', {}).get(orderpoint.id, False)
                        if origins:
                            origins = self.env['stock.reference'].browse(origins)
                            origin = '%s - %s' % (orderpoint.display_name, ','.join(origins.mapped('name')))
                        else:
                            origin = orderpoint.name
                        if orderpoint.product_uom.compare(orderpoint.qty_to_order, 0.0) == 1:
                            date = orderpoint._get_orderpoint_procurement_date()
                            global_horizon_days = orderpoint.get_horizon_days()
                            if global_horizon_days:
                                date -= relativedelta.relativedelta(days=int(global_horizon_days))
                            values = orderpoint._prepare_procurement_values(date=date)
                            procurements.append(self.env['stock.rule'].Procurement(
                                orderpoint.product_id, orderpoint.qty_to_order, orderpoint.product_uom,
                                orderpoint.location_id, orderpoint.name, origin,
                                orderpoint.company_id, values))

                    try:
                        with self.env.cr.savepoint():
                            self.env['stock.rule'].with_context(from_orderpoint=True).run(procurements, raise_user_error=raise_user_error)
                    except ProcurementException as errors:
                        orderpoints_exceptions = []
                        for procurement, error_msg in errors.procurement_exceptions:
                            orderpoints_exceptions += [(procurement.values.get('orderpoint_id'), error_msg)]
                        all_orderpoints_exceptions += orderpoints_exceptions
                        failed_orderpoints = self.env['stock.warehouse.orderpoint'].concat(*[o[0] for o in orderpoints_exceptions])
                        if not failed_orderpoints:
                            _logger.error('Unable to process orderpoints')
                            break
                        orderpoints_batch -= failed_orderpoints

                    except OperationalError:
                        if use_new_cursor:
                            cr.rollback()
                            continue
                        else:
                            raise
                    else:
                        orderpoints_batch._post_process_scheduler()
                        break

                # Log an activity on product template for failed orderpoints.
                for orderpoint, error_msg in all_orderpoints_exceptions:
                    existing_activity = self.env['mail.activity'].search_count([
                        ('res_id', '=', orderpoint.product_id.product_tmpl_id.id),
                        ('res_model_id', '=', self.env.ref('product.model_product_template').id),
                        ('note', 'like', error_msg)], limit=1)
                    if not existing_activity:
                        orderpoint.product_id.product_tmpl_id.sudo().activity_schedule(
                            'mail.mail_activity_data_warning',
                            note=error_msg,
                            user_id=orderpoint.product_id.responsible_id.id or SUPERUSER_ID,
                        )

            finally:
                if use_new_cursor:
                    try:
                        cr.commit()
                    finally:
                        cr.close()
                    _logger.info("A batch of %d orderpoints is processed and committed", len(orderpoints_batch_ids))

        return {}