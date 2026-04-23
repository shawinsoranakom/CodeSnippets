def test_hr_version_fields_tracking(self):
        tracking_blacklist = {
            "__last_update",
            "active_employee",
            "activity_ids",
            "company_country_id",
            "contract_wage",
            "country_code",
            "create_date",
            "create_uid",
            "currency_id",
            "date_end",
            "date_start",
            "departure_description",
            "display_name",
            "id",
            "is_current",
            "is_flexible",
            "is_fully_flexible",
            "is_future",
            "is_in_contract",
            "is_past",
            "job_title",
            "last_modified_date",
            "last_modified_on",
            "last_modified_uid",
            "member_of_department",
            "message_follower_ids",
            "message_ids",
            "message_partner_ids",
            "rating_ids",
            "template_warning",
            "tz",
            "website_message_ids",
            "work_location_name",
            "work_location_type",
            "write_date",
            "write_uid",
        }

        hr_version_model = self.env['hr.version']
        fields_without_tracking = []

        for field_name, field in hr_version_model._fields.items():
            if field_name in tracking_blacklist:
                continue
            if field.compute and not field.inverse:
                continue
            if field.related:
                continue
            if hasattr(field, 'store') and field.store is False:
                continue
            if hasattr(field, 'tracking') and not field.tracking:
                fields_without_tracking.append(field_name)

        self.assertFalse(
            fields_without_tracking,
            f"The following hr.version fields should have tracking=True: {fields_without_tracking}",
        )