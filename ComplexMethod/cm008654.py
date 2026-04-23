def _call_graphql_api(
        self, operation, video_id, query,
        variables: dict[str, tuple[str, str]] | None = None,
        note='Downloading GraphQL JSON metadata',
    ):
        parameters = ''
        if variables:
            parameters = ', '.join(f'${name}: {type_}' for name, (type_, _) in variables.items())
            parameters = f'({parameters})'

        result = self._download_json('https://graph.telewebion.com/graphql', video_id, note, data=json.dumps({
            'operationName': operation,
            'query': f'query {operation}{parameters} @cacheControl(maxAge: 60) {{{query}\n}}\n',
            'variables': {name: value for name, (_, value) in (variables or {}).items()},
        }, separators=(',', ':')).encode(), headers={
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        })
        if not result or traverse_obj(result, 'errors'):
            message = ', '.join(traverse_obj(result, ('errors', ..., 'message', {str})))
            raise ExtractorError(message or 'Unknown GraphQL API error')

        return result['data']