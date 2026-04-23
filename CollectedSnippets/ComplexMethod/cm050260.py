def _test_payroll_fields_are_hidden_to_non_payroll_users(self, model_name, view_id, payroll_page_name):
        form_view = self.env.ref(view_id)
        form_view_get_result = self.env['hr.employee'].get_view(form_view.id, 'form')
        form_view_arch = form_view_get_result['arch']
        node = etree.fromstring(form_view_arch)
        self.assertTrue(node.xpath(f"//page[@name='{payroll_page_name}']"), f"[{model_name}] Payroll page should be found in the form view.")
        payroll_field_node_list = node.xpath(f"//page[@name='{payroll_page_name}']//field[not(ancestor::field)]")
        self.assertTrue(payroll_field_node_list, f"[{model_name}] At least one field should be found inside Payroll information page.")
        payroll_field_names = [
            payroll_field_node.attrib['name']
            for payroll_field_node in payroll_field_node_list
        ]
        current_payroll_field_names = {
            f_name
            for f_name, field in self.env[model_name]._fields.items()
            if field.groups and ('hr.group_hr_manager' in field.groups or 'hr_payroll.group_hr_payroll_user' in field.groups)
        }
        whitelist_field_names = [
            'resource_calendar_id',
            'employee_type',
            'tz',
            'currency_id',
            'lang',
            'registration_number',
            'standard_calendar_id',
            'employee_age',
            'distance_home_work',
            'distance_home_work_unit',
            'show_billable_time_target',
            'billable_time_target',
            'holidays',
            'car_id',
            'new_car',
            'new_car_model_id',
            'ordered_car_id',
            'fuel_type',
            'transport_mode_bike',
            'bike_id',
            'new_bike',
            'new_bike_model_id',
            'originated_offer_id',
            'is_non_resident',
            'structure_id'
        ]
        missing_group_field_names = [
            f_name
            for f_name in payroll_field_names
            if f_name not in current_payroll_field_names and f_name not in whitelist_field_names
        ]
        self.assertFalse(
            missing_group_field_names,
            "[{}] Missing payroll group on following fields: \n - {}".format(
                model_name,
                '\n - '.join(missing_group_field_names),
            ),
        )