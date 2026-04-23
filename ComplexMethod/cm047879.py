def _get_replenishment_receipt(self, doc_in, components):
        if doc_in._name == 'stock.picking':
            return self._format_receipt_date('expected', doc_in.scheduled_date)

        if doc_in._name == 'mrp.production':
            max_date_start = doc_in.date_start
            all_available = True
            some_unavailable = False
            some_estimated = False
            for component in components:
                if component['summary']['receipt']['date']:
                    max_date_start = max(max_date_start, component['summary']['receipt']['date'])
                all_available = all_available and component['summary']['receipt']['type'] == 'available'
                some_unavailable = some_unavailable or component['summary']['receipt']['type'] == 'unavailable'
                some_estimated = some_estimated or component['summary']['receipt']['type'] == 'estimated'

            if some_unavailable:
                return self._format_receipt_date('unavailable')
            if all_available:
                return self._format_receipt_date('expected', doc_in.date_finished)

            new_date = max_date_start + timedelta(days=doc_in.bom_id.produce_delay)
            receipt_state = 'estimated' if some_estimated else 'expected'
            return self._format_receipt_date(receipt_state, new_date)
        return self._format_receipt_date('unavailable')