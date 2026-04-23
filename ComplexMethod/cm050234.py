def add_to_report(report, records, available=True, reason=''):
    """ Add records to the report with the provided values.

        Structure of the report:
        report = {
            'providers': {
                provider_record : {
                    'available': true|false,
                    'reason': "",
                },
            },
            'payment_methods': {
                pm_record : {
                    'available': true|false,
                    'reason': "",
                    'supported_providers': [(provider_record, report['providers'][p]['available'])],
                },
            },
        }

    :param dict report: The availability report for providers and payment methods.
    :param payment.provider|payment.method records: The records to add to the report.
    :param bool available: Whether the records are available.
    :param str reason: The reason for which records are not available, if any.
    :return: None
    """
    if report is None or not records:  # The report might not be initialized, or no records to add.
        return

    category = 'providers' if records._name == 'payment.provider' else 'payment_methods'
    report.setdefault(category, {})
    for r in records:
        report[category][r] = {
            'available': available,
            'reason': reason,
        }
        if category == 'payment_methods' and 'providers' in report:
            report[category][r]['supported_providers'] = [
                (p, report['providers'][p]['available'])
                for p in r.provider_ids if p in report['providers']
            ]