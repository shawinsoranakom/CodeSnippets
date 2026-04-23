def open_kiosk_mode(self, token, from_trial_mode=False):
        company = self._get_company(token)
        if not company:
            return request.not_found()
        else:
            department_list = [
                {"id": dep["id"], "name": dep["name"], "count": dep["total_employee"]}
                for dep in request.env["hr.department"]
                .with_context(allowed_company_ids=[company.id])
                .sudo()
                .search_read(
                    domain=[("company_id", "=", company.id)],
                    fields=["id", "name", "total_employee"],
                )
            ]
            has_password = self.has_password()
            if not from_trial_mode and has_password:
                request.session.logout(keep_db=True)
            if (from_trial_mode or (not has_password and not request.env.user.is_public)):
                kiosk_mode = "settings"
            else:
                kiosk_mode = company.attendance_kiosk_mode
            version_info = exp_version()
            return request.render(
                'hr_attendance.public_kiosk_mode',
                {
                    'kiosk_backend_info': {
                        'token': token,
                        'company_id': company.id,
                        'company_name': company.name,
                        'departments': department_list,
                        'kiosk_mode': kiosk_mode,
                        'from_trial_mode': from_trial_mode,
                        'barcode_source': company.attendance_barcode_source,
                        'device_tracking_enabled': company.attendance_device_tracking,
                        'lang': py_to_js_locale(company.partner_id.lang or company.env.lang),
                        'server_version_info': version_info.get('server_version_info'),
                    },
                }
            )