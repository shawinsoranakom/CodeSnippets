def _get_message_dict(self):
        """ Return a dict with the different possible message used for the
        rule message. It should return one message for each stock.rule action
        (except push and pull). This function is override in mrp and
        purchase_stock in order to complete the dictionary.
        """
        message_dict = {}
        source, destination, direct_destination, operation = self._get_message_values()
        if self.action in ('push', 'pull', 'pull_push'):
            suffix = ""
            if self.action in ('pull', 'pull_push') and direct_destination and not self.location_dest_from_rule:
                suffix = _("<br>The products will be moved towards <b>%(destination)s</b>, <br/> as specified from <b>%(operation)s</b> destination.", destination=direct_destination, operation=operation)
            if self.procure_method == 'make_to_order' and self.location_src_id:
                suffix += _("<br>A need is created in <b>%s</b> and a rule will be triggered to fulfill it.", source)
            if self.procure_method == 'mts_else_mto' and self.location_src_id:
                suffix += _("<br>If the products are not available in <b>%s</b>, a rule will be triggered to bring the missing quantity in this location.", source)
            message_dict = {
                'pull': _(
                    'When products are needed in <b>%(destination)s</b>, <br> <b>%(operation)s</b> are created from <b>%(source_location)s</b> to fulfill the need. %(suffix)s',
                    destination=destination,
                    operation=operation,
                    source_location=source,
                    suffix=suffix,
                ),
                'push': _(
                    'When products arrive in <b>%(source_location)s</b>, <br> <b>%(operation)s</b> are created to send them to <b>%(destination)s</b>.',
                    source_location=source,
                    operation=operation,
                    destination=destination,
                ),
            }
        return message_dict