def _myinvois_get_submission_status(self):
        """
        Fetches the status of the submissions in self.

        :return: A dict of the format: {submission_uid: {'error': '', 'statuses': {record: document_statuses}}}
        """
        def _make_deep_default_dict():
            return defaultdict(_make_deep_default_dict)

        if not self:
            return None

        results = _make_deep_default_dict()
        for proxy_user, records in self.grouped(lambda r: r._myinvois_get_proxy_user()).items():
            if not proxy_user:
                continue

            for submission_uid, submission_records in records.grouped('myinvois_submission_uid').items():
                # Filter the submission records to skip batches that we don't want to fetch yet.
                submission_records.filtered(lambda r: not r.myinvois_retry_at or fields.Datetime.from_string(r.myinvois_retry_at) <= datetime.datetime.now())

                if not submission_uid or not submission_records:
                    continue

                self.env["res.company"]._with_locked_records(submission_records)

                records_per_uuid = submission_records.grouped('myinvois_external_uuid')

                result = proxy_user._l10n_my_edi_contact_proxy(
                    endpoint='api/l10n_my_edi/1/get_submission_statuses',
                    params={
                        'submission_uid': submission_uid,
                        'page': 1,
                    },
                )
                if 'error' in result:
                    results[submission_uid]['error'] = self._myinvois_map_error(result['error'])
                else:
                    # While unlikely, if we end up with too many documents we will start by getting all the info.
                    if result['document_count'] > 100:
                        for page in range(2, (result['document_count'] // 100) + 1):
                            if self._can_commit():  # avoid the sleep in tests.
                                time.sleep(0.3)
                            page_result = proxy_user._l10n_my_edi_contact_proxy(
                                endpoint='api/l10n_my_edi/1/get_submission_statuses',
                                params={
                                    'submission_uid': submission_uid,
                                    'page': page,
                                },
                            )
                            result['statuses'].update(page_result['statuses'])

                    for uuid, status in result['statuses'].items():
                        record = records_per_uuid.get(uuid)
                        if record:
                            results[submission_uid]['statuses'][record] = status

                if self._can_commit():  # avoid the sleep in tests.
                    time.sleep(0.3)
        return results