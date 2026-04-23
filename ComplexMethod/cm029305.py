def _check_event_names_dont_overlap():
	"""
	check that event names defined in this file are valid and non-overlapping
	(naiively n^2 so it's pretty slow but ok for now, optimize when >20 events)
	"""
	event_names = {
		name.split('[')[0]
		for name in globals().keys()
		if not name.startswith('_')
		and inspect.isclass(globals()[name])
		and issubclass(globals()[name], BaseEvent)
		and name != 'BaseEvent'
	}
	for name_a in event_names:
		assert name_a.endswith('Event'), f'Event with name {name_a} does not end with "Event"'
		for name_b in event_names:
			if name_a != name_b:  # Skip self-comparison
				assert name_a not in name_b, (
					f'Event with name {name_a} is a substring of {name_b}, all events must be completely unique to avoid find-and-replace accidents'
				)