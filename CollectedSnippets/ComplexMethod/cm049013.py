def generate_qr_codes_page(self):
        """
        Generate the data needed to print the QR codes page
        """
        name = ""
        url = url_unquote(self.pos_config_id._get_self_order_url())
        if self.pos_self_ordering_mode == 'mobile' and self.pos_module_pos_restaurant:
            table_ids = self.pos_config_id.floor_ids.table_ids
            if not table_ids:
                raise ValidationError(_("In Self-Order mode, you must have at least one table to generate QR codes"))

            if self.pos_self_ordering_service_mode == 'table':
                url = url_unquote(self.pos_config_id._get_self_order_url(table_ids[0].id))
                name = table_ids[0].table_number

        return self.env.ref("pos_self_order.report_self_order_qr_codes_page").report_action(
            [], data={
                'pos_name': self.pos_config_id.name,
                'floors': [
                    {
                        "name": floor.get("name"),
                        "type": floor.get("type"),
                        "table_rows": list(split_every(3, floor["tables"], list)),
                    }
                    for floor in self.pos_config_id._get_qr_code_data()
                ],
                'table_mode': self.pos_self_ordering_mode and self.pos_module_pos_restaurant and self.pos_self_ordering_service_mode == 'table',
                'self_order': self.pos_self_ordering_mode == 'mobile',
                'table_example': {
                    'name': name,
                    'decoded_url': url or "",
                }
            }
        )