def rule_failed(rule, exc_info):
    exception(u'Rule {}'.format(rule.name), exc_info)