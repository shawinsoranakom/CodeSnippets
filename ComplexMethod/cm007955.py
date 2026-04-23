def details_from_prefix(prefix):
        if not prefix:
            return CommitGroup.CORE, None, ()

        prefix, *sub_details = prefix.split(':')

        group, details = CommitGroup.get(prefix)
        if group is CommitGroup.PRIORITY and details:
            details = details.partition('/')[2].strip()

        if details and '/' in details:
            logger.error(f'Prefix is overnested, using first part: {prefix}')
            details = details.partition('/')[0].strip()

        if details == 'common':
            details = None
        elif group is CommitGroup.NETWORKING and details == 'rh':
            details = 'Request Handler'

        return group, details, sub_details