def read_config_open_orders(self, domain, record_ids=[]):
        delete_record_ids = {}
        dynamic_records = {}

        for model, dom in domain.items():
            ids = record_ids.get(model, [])
            browsed = self.env[model].browse(ids)

            dynamic_records[model] = self.env[model].search(dom)
            delete_record_ids[model] = browsed.filtered(lambda r: not r.exists()).ids
            # Cancelled orders must be forced deleted from the user interface.
            if model == "pos.order":
                delete_record_ids[model] += browsed.exists().filtered(lambda r: r.state == "cancel").ids

        pos_order_data = dynamic_records.get('pos.order') or self.env['pos.order']
        data = pos_order_data.read_pos_data([], self)

        for key, records in dynamic_records.items():
            fields = self.env[key]._load_pos_data_fields(self)
            ids = list(set(records.ids + [record['id'] for record in data.get(key, [])]))
            dynamic_records[key] = self.env[key].browse(ids).read(fields, load=False)

        for key, value in data.items():
            if key not in dynamic_records:
                dynamic_records[key] = value

        return {
            'dynamic_records': dynamic_records,
            'deleted_record_ids': delete_record_ids,
        }