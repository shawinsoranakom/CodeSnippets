def _update_matching_number(self, amls):
        amls = amls._all_reconciled_lines()
        all_partials = amls.matched_debit_ids | amls.matched_credit_ids

        # The matchings form a set of graphs, which can be numbered: this is the matching number.
        # We iterate on each edge of the graphs, giving it a number (min of its edge ids).
        # By iterating, we either simply add a node (move line) to the graph and asign the number to
        # it or we merge the two graphs.
        # At the end, we have an index for the number to assign of all lines.
        number2lines = {}
        line2number = {}
        for partial in all_partials.sorted('id'):
            debit_min_id = line2number.get(partial.debit_move_id.id)
            credit_min_id = line2number.get(partial.credit_move_id.id)
            if debit_min_id and credit_min_id:  # merging the 2 graph into the one with smalles number
                if debit_min_id != credit_min_id:
                    min_min_id = min(debit_min_id, credit_min_id)
                    max_min_id = max(debit_min_id, credit_min_id)
                    for line_id in number2lines[max_min_id]:
                        line2number[line_id] = min_min_id
                    number2lines[min_min_id].extend(number2lines.pop(max_min_id))
            elif debit_min_id:  # adding a new node to a graph
                number2lines[debit_min_id].append(partial.credit_move_id.id)
                line2number[partial.credit_move_id.id] = debit_min_id
            elif credit_min_id:  # adding a new node to a graph
                number2lines[credit_min_id].append(partial.debit_move_id.id)
                line2number[partial.debit_move_id.id] = credit_min_id
            else:  # creating a new graph
                number2lines[partial.id] = [partial.debit_move_id.id, partial.credit_move_id.id]
                line2number[partial.debit_move_id.id] = partial.id
                line2number[partial.credit_move_id.id] = partial.id

        amls.flush_recordset(['full_reconcile_id'])
        self.env.cr.execute_values("""
            UPDATE account_move_line l
               SET matching_number = CASE
                       WHEN l.full_reconcile_id IS NOT NULL THEN l.full_reconcile_id::text
                       ELSE 'P' || source.number
                   END
              FROM (VALUES %s) AS source(number, ids)
             WHERE l.id = ANY(source.ids)
        """, list(number2lines.items()), page_size=1000)
        processed_amls = self.env['account.move.line'].browse([_id for ids in number2lines.values() for _id in ids])
        processed_amls.invalidate_recordset(['matching_number'])
        (amls - processed_amls).matching_number = False