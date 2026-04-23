def apply_on_before_component_callbacks(self):
        for script in self.scripts:
            on_before = script.on_before_component_elem_id or []
            on_after = script.on_after_component_elem_id or []

            for elem_id, callback in on_before:
                if elem_id not in self.on_before_component_elem_id:
                    self.on_before_component_elem_id[elem_id] = []

                self.on_before_component_elem_id[elem_id].append((callback, script))

            for elem_id, callback in on_after:
                if elem_id not in self.on_after_component_elem_id:
                    self.on_after_component_elem_id[elem_id] = []

                self.on_after_component_elem_id[elem_id].append((callback, script))

            on_before.clear()
            on_after.clear()