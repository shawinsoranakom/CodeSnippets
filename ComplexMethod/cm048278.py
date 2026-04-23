def _get_less_active_operator(self, operator_statuses, operators):
        """ Retrieve the most available operator based on the following criteria:
        - Lowest number of active chats.
        - Not in  a call.
        - If an operator is in a call and has two or more active chats, don't
          give priority over an operator with more conversations who is not in a
          call.

        :param operator_statuses: list of dictionaries containing the operator's
            id, the number of active chats and a boolean indicating if the
            operator is in a call. The list is ordered by the number of active
            chats (ascending) and whether the operator is in a call
            (descending).
        :param operators: recordset of :class:`ResUsers` operators to choose from.
        :return: the :class:`ResUsers` record for the chosen operator
        """
        if not operators:
            return False

        # 1) only consider operators in the list to choose from
        operator_statuses = [
            s for s in operator_statuses if s['partner_id'] in set(operators.partner_id.ids)
        ]

        # 2) try to select an inactive op, i.e. one w/ no active status (no recent chat)
        active_op_partner_ids = {s['partner_id'] for s in operator_statuses}
        candidates = operators.filtered(lambda o: o.partner_id.id not in active_op_partner_ids)
        if candidates:
            return random.choice(candidates)

        # 3) otherwise select least active ops, based on status ordering (count + in_call)
        best_status = operator_statuses[0]
        best_status_op_partner_ids = {
            s['partner_id']
            for s in operator_statuses
            if (s['count'], s['in_call']) == (best_status['count'], best_status['in_call'])
        }
        candidates = operators.filtered(lambda o: o.partner_id.id in best_status_op_partner_ids)
        return random.choice(candidates)