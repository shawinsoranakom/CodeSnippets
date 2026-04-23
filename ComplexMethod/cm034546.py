def from_dict(data: dict[str, t.Any]) -> Feature:
        title = data.get('title')
        summary = data.get('summary')
        component = data.get('component')
        labels = data.get('labels')
        assignee = data.get('assignee')

        if not isinstance(title, str):
            raise RuntimeError(f'`title` is not `str`: {title}')

        if not isinstance(summary, str):
            raise RuntimeError(f'`summary` is not `str`: {summary}')

        if not isinstance(component, str):
            raise RuntimeError(f'`component` is not `str`: {component}')

        if not isinstance(assignee, (str, type(None))):
            raise RuntimeError(f'`assignee` is not `str`: {assignee}')

        if not isinstance(labels, list) or not all(isinstance(item, str) for item in labels):
            raise RuntimeError(f'`labels` is not `list[str]`: {labels}')

        return Feature(
            title=title,
            summary=summary,
            component=component,
            labels=labels,
            assignee=assignee,
        )