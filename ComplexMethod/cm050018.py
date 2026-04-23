def check_recent_application(self, field, value, job_id):
        def refused_applicants_condition(applicant):
            return not applicant.active \
                and applicant.job_id.id == int(job_id) \
                and applicant.create_date >= (datetime.now() - relativedelta(months=6))

        field_domain = {
            'name': [('partner_name', '=ilike', escape_psql(value))],
            'email': [('email_normalized', '=', email_normalize(value))],
            'phone': [('partner_phone', '=', value)],
            'linkedin': [('linkedin_profile', '=ilike', escape_psql(value))],
        }.get(field, [])

        applications_by_status = http.request.env['hr.applicant'].sudo().search(Domain.AND([
            field_domain,
            [
                ('job_id.website_id', 'in', [http.request.website.id, False]),
                '|',
                    ('application_status', '=', 'ongoing'),
                    '&',
                        ('application_status', '=', 'refused'),
                        ('active', '=', False),
            ]
        ]), order='create_date DESC').grouped('application_status')
        refused_applicants = applications_by_status.get('refused', http.request.env['hr.applicant'])
        if any(applicant for applicant in refused_applicants if refused_applicants_condition(applicant)):
            return {
                'message':  _(
                    'We\'ve found a previous closed application in our system within the last 6 months.'
                    ' Please consider before applying in order not to duplicate efforts.'
                )
            }

        if 'ongoing' not in applications_by_status:
            return {'message': None}

        ongoing_application = applications_by_status.get('ongoing')[0]
        if ongoing_application.job_id.id == int(job_id):
            recruiter_contact = "" if not ongoing_application.user_id else _(
                ' In case of issue, contact %(contact_infos)s',
                contact_infos=", ".join(
                    [value for value in itemgetter('name', 'email', 'phone')(ongoing_application.user_id) if value]
                ))
            return {
                'message':  _(
                    'An application already exists for %(value)s.'
                    ' Duplicates might be rejected. %(recruiter_contact)s',
                    value=value,
                    recruiter_contact=recruiter_contact
                )
            }

        return {
            'message':  _(
                'We found a recent application with a similar name, email, phone number.'
                ' You can continue if it\'s not a mistake.'
            )
        }