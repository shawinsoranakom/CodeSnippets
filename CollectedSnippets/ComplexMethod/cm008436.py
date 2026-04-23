def _graphql_to_legacy(self, data, twid):
        result = traverse_obj(data, ('tweetResult', 'result', {dict})) or {}

        typename = result.get('__typename')
        if typename not in ('Tweet', 'TweetWithVisibilityResults', 'TweetTombstone', 'TweetUnavailable', None):
            self.report_warning(f'Unknown typename: {typename}', twid, only_once=True)

        if 'tombstone' in result:
            cause = remove_end(traverse_obj(result, ('tombstone', 'text', 'text', {str})), '. Learn more')
            raise ExtractorError(f'Twitter API says: {cause or "Unknown error"}', expected=True)
        elif typename == 'TweetUnavailable':
            reason = result.get('reason')
            if reason in ('NsfwLoggedOut', 'NsfwViewerHasNoStatedAge'):
                self.raise_login_required('NSFW tweet requires authentication')
            elif reason == 'Protected':
                self.raise_login_required('You are not authorized to view this protected tweet')
            raise ExtractorError(reason or 'Requested tweet is unavailable', expected=True)
        # Result for "stale tweet" needs additional transformation
        elif typename == 'TweetWithVisibilityResults':
            result = traverse_obj(result, ('tweet', {dict})) or {}

        status = result.get('legacy', {})
        status.update(traverse_obj(result, {
            'user': ('core', 'user_results', 'result', 'legacy'),
            'card': ('card', 'legacy'),
            'quoted_status': ('quoted_status_result', 'result', 'legacy'),
            'retweeted_status': ('legacy', 'retweeted_status_result', 'result', 'legacy'),
        }, expected_type=dict, default={}))

        # extra transformations needed since result does not match legacy format
        if status.get('retweeted_status'):
            status['retweeted_status']['user'] = traverse_obj(status, (
                'retweeted_status_result', 'result', 'core', 'user_results', 'result', 'legacy', {dict})) or {}

        binding_values = {
            binding_value.get('key'): binding_value.get('value')
            for binding_value in traverse_obj(status, ('card', 'binding_values', ..., {dict}))
        }
        if binding_values:
            status['card']['binding_values'] = binding_values

        return status