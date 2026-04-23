def dispatch(self, event_type: EventType, **event_data):
        if event_type == EventType.MouseMotionEvent:
            self.mouse_point = event_data["point"]
        elif event_type == EventType.MouseDragEvent:
            self.mouse_drag_point = event_data["point"]
        elif event_type == EventType.KeyPressEvent:
            self.pressed_keys.add(event_data["symbol"])  # Modifiers?
        elif event_type == EventType.KeyReleaseEvent:
            self.pressed_keys.difference_update({event_data["symbol"]})  # Modifiers?
        elif event_type == EventType.MousePressEvent:
            self.draggable_object_listners = [
                listner
                for listner in self.event_listners[EventType.MouseDragEvent]
                if listner.mobject.is_point_touching(self.mouse_point)
            ]
        elif event_type == EventType.MouseReleaseEvent:
            self.draggable_object_listners = []

        propagate_event = None

        if event_type == EventType.MouseDragEvent:
            for listner in self.draggable_object_listners:
                assert isinstance(listner, EventListener)
                propagate_event = listner.callback(listner.mobject, event_data)
                if propagate_event is not None and propagate_event is False:
                    return propagate_event

        elif event_type.value.startswith('mouse'):
            for listner in self.event_listners[event_type]:
                if listner.mobject.is_point_touching(self.mouse_point):
                    propagate_event = listner.callback(
                        listner.mobject, event_data)
                    if propagate_event is not None and propagate_event is False:
                        return propagate_event

        elif event_type.value.startswith('key'):
            for listner in self.event_listners[event_type]:
                propagate_event = listner.callback(listner.mobject, event_data)
                if propagate_event is not None and propagate_event is False:
                    return propagate_event

        return propagate_event