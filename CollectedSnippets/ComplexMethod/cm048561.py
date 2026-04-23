def _compute_report_option_filter(self, field_name, default_value=False):
        # We don't depend on the different filter fields on the root report, as we don't want a manual change on it to be reflected on all the reports
        # using it as their root (would create confusion). The root report filters are only used as some kind of default values.
        # When a report is a section, it can also get its default filter values from its parent composite report. This only happens when we're sure
        # the report is not used as a section of multiple reports, nor as a standalone report.
        for report in self.sorted(lambda x: not x.section_report_ids):
            # Reports are sorted in order to first treat the composite reports, in case they need to compute their filters a the same time
            # as their sections
            is_accessible = self.env['ir.actions.client'].search_count([('context', 'ilike', f"'report_id': {report.id}"), ('tag', '=', 'account_report')])
            is_variant = bool(report.root_report_id)
            if (is_accessible or is_variant) and report.section_main_report_ids:
                continue  # prevent updating the filters of a report when being added as a section of a report
            if report.root_report_id:
                report[field_name] = report.root_report_id[field_name]
            elif len(report.section_main_report_ids) == 1 and not is_accessible:
                report[field_name] = report.section_main_report_ids[field_name]
            else:
                report[field_name] = default_value