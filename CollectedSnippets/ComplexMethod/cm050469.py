def sync_from_ui(self, orders):
        """ Create and update Orders from the frontend PoS application.

        Create new orders and update orders that are in draft status. If an order already exists with a status
        different from 'draft' it will be discarded, otherwise it will be saved to the database. If saved with
        'draft' status the order can be overwritten later by this function.

        :param orders: dictionary with the orders to be created.
        :type orders: dict.
        :returns: list of db-ids for the created and updated orders.
        :rtype: list
        """
        sync_token = randrange(100_000_000)  # Use to differentiate 2 parallels calls to this function in the logs
        _logger.info("PoS synchronisation #%d started for PoS orders references: %s", sync_token, [self._get_order_log_representation(order) for order in orders])
        order_ids = []

        for order in orders:
            order_log_name = self._get_order_log_representation(order)
            _logger.debug("PoS synchronisation #%d processing order %s order full data: %s", sync_token, order_log_name, pformat(order))

            refunded_orders = self._get_refunded_orders(order)
            if len(refunded_orders) > 1:
                raise ValidationError(_('You can only refund products from the same order.'))
            elif len(refunded_orders) == 1:
                order_ids.append(refunded_orders[0].id)

            existing_order = self._get_open_order(order)
            if existing_order and existing_order.state == 'draft':
                existing_order._ensure_to_keep_last_preparation_change(order)
                order_ids.append(self._process_order(order, existing_order))
                _logger.info("PoS synchronisation #%d order %s updated pos.order #%d", sync_token, order_log_name, order_ids[-1])
            elif not existing_order:
                order_ids.append(self._process_order(order, False))
                _logger.info("PoS synchronisation #%d order %s created pos.order #%d", sync_token, order_log_name, order_ids[-1])
            else:
                # In theory, this situation is unintended
                # In practice it can happen when "Tip later" option is used
                existing_order._ensure_to_keep_last_preparation_change(order)
                order_ids.append(existing_order.id)
                _logger.info("PoS synchronisation #%d order %s sync ignored for existing PoS order %s (state: %s)", sync_token, order_log_name, existing_order, existing_order.state)

        # Sometime pos_orders_ids can be empty.
        pos_order_ids = self.env['pos.order'].browse(order_ids)
        config = pos_order_ids.config_id[0] if pos_order_ids else False

        for order in pos_order_ids:
            order._ensure_access_token()
            if not self.env.context.get('preparation'):
                order.config_id.notify_synchronisation(order.config_id.current_session_id.id, self.env.context.get('device_identifier', 0))

        _logger.info("PoS synchronisation #%d finished", sync_token)
        return pos_order_ids.read_pos_data(orders, config)