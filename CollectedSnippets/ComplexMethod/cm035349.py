def get_condensation(self, view: View) -> Condensation:
        target_size = self.max_size // 2
        head_event_ids = [event.id for event in view.events[: self.keep_first]]

        events_from_tail = target_size - len(head_event_ids)

        message: str = """You will be given a list of actions, observations, and thoughts from a coding agent.
        Each item in the list has an identifier. Please sort the identifiers in order of how important the
        contents of the item are for the next step of the coding agent's task, from most important to least
        important."""

        response = self.llm.completion(
            messages=[
                {'content': message, 'role': 'user'},
                *[
                    {
                        'content': f'<ID>{e.id}</ID>\n<CONTENT>{e.message}</CONTENT>',
                        'role': 'user',
                    }
                    for e in view
                ],
            ],
            response_format={
                'type': 'json_schema',
                'json_schema': {
                    'name': 'ImportantEventSelection',
                    'schema': ImportantEventSelection.model_json_schema(),
                },
            },
        )

        response_ids = ImportantEventSelection.model_validate_json(
            response.choices[0].message.content
        ).ids

        self.add_metadata('metrics', self.llm.metrics.get())

        # Filter out any IDs from the head and trim the results down
        response_ids = [
            response_id
            for response_id in response_ids
            if response_id not in head_event_ids
        ][:events_from_tail]

        # If the response IDs aren't _long_ enough, iterate backwards through the events and add any unfound IDs to the list.
        for event in reversed(view):
            if len(response_ids) >= events_from_tail:
                break
            if event.id not in response_ids:
                response_ids.append(event.id)

        # Now that we've found the right number of events to keep, convert this into a list of events to forget.
        event = CondensationAction(
            forgotten_event_ids=[
                event.id
                for event in view
                if event.id not in response_ids and event.id not in head_event_ids
            ],
        )

        return Condensation(action=event)