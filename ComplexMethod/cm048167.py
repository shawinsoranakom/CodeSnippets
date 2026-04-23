def get_views(self, views, options=None):
        res = super().get_views(views, options)
        if options and options.get('toolbar'):
            wip_report_id = None

            def get_wip_report_id():
                return self.env['ir.model.data']._xmlid_to_res_id("mrp_account.wip_report", raise_if_not_found=False)

            for view_data in res['views'].values():
                print_data_list = view_data.get('toolbar', {}).get('print')
                if print_data_list:
                    if wip_report_id is None and re.search(r'widget="timesheet_uom(\w)*"', view_data['arch']):
                        wip_report_id = get_wip_report_id()
                    if wip_report_id:
                        view_data['toolbar']['print'] = [print_data for print_data in print_data_list if print_data['id'] != wip_report_id]
        return res