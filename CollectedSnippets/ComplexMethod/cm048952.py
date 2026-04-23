def _test_13_mock(self, endpoint, params):
        if endpoint == 'api/l10n_my_edi/1/submit_invoices':
            res = {
                'submission_uid': '123456789',
                'documents': [],
            }
            for i, document in enumerate(params['documents']):
                res['documents'].append({
                    'move_id': document['move_id'],
                    'uuid': f'12345897451351{i}',
                    'success': True,
                })
            return res
        if endpoint == 'api/l10n_my_edi/1/get_submission_statuses' and self.submission_status_count == 0:
            return {
                'statuses': {
                    '123458974513510': {
                        'status': 'in_progress',
                        'reason': '',
                        'long_id': '',
                        'valid_datetime': '',
                    },
                    '123458974513511': {
                        'status': 'in_progress',
                        'reason': '',
                        'long_id': '',
                        'valid_datetime': '',
                    },
                    '123458974513512': {
                        'status': 'in_progress',
                        'reason': '',
                        'long_id': '',
                        'valid_datetime': '',
                    },
                    '123458974513513': {
                        'status': 'in_progress',
                        'reason': '',
                        'long_id': '',
                        'valid_datetime': '',
                    },
                    '123458974513514': {
                        'status': 'in_progress',
                        'reason': '',
                        'long_id': '',
                        'valid_datetime': '',
                    },
                },
                'document_count': 5,
            }
        if endpoint == 'api/l10n_my_edi/1/get_submission_statuses' and self.submission_status_count in [1, 3]:
            res = {'statuses': {}, 'document_count': 10}
            # Build the res using loops otherwise it'd take a lot of lines.
            for i in range(2):
                for j in range(5):
                    res['statuses'][f'1234589745135{i}{j}'] = {
                        'status': 'valid',
                        'reason': '',
                        'long_id': '123-789-654',
                        'valid_datetime': '2024-07-15T05:00:00Z',
                    }
            return res
        raise UserError('Unexpected endpoint called during a test: %s with params %s.' % (endpoint, params))