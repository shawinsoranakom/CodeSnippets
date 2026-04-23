def job_filtering_condition(job, filter_to_disable=False):
            country_filter = country if (country and filter_to_disable != 'country_id') else None
            field_filters = {
                'department_id': department.id,
                'address_id': office.id,
                'industry_id': industry.id,
                'contract_type_id': contract_type.id,
            }

            all_fields = all(
                job[job_field].id == value
                for job_field, value in field_filters.items()
                if job_field != filter_to_disable and value
            )
            if not all_fields or (
                country_filter and not (
                    job.address_id and job.address_id.country_id == country
                )
            ):
                return False
            not_exist_filter = {
                'department_id': is_other_department,
                'address_id': is_remote and filter_to_disable != 'country_id',
                'industry_id': is_industry_untyped,
                'contract_type_id': is_untyped,
            }
            return all(
                not job[job_field]
                for job_field, value in not_exist_filter.items()
                if job_field != filter_to_disable and value
            )