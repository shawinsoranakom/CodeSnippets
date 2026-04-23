def format_single_change(self, info: CommitInfo):
        message, sep, rest = info.message.partition('\n')
        if '[' not in message:
            # If the message doesn't already contain markdown links, try to add a link to the commit
            message = self._format_message_link(message, info.commit.hash)

        if info.issues:
            message = f'{message} ({self._format_issues(info.issues)})'

        if info.commit.authors:
            message = f'{message} by {self._format_authors(info.commit.authors)}'

        if info.fixes:
            fix_message = ', '.join(f'{self._format_message_link(None, fix.hash)}' for fix in info.fixes)

            authors = sorted({author for fix in info.fixes for author in fix.authors}, key=str.casefold)
            if authors != info.commit.authors:
                fix_message = f'{fix_message} by {self._format_authors(authors)}'

            message = f'{message} (With fixes in {fix_message})'

        return message if not sep else f'{message}{sep}{rest}'