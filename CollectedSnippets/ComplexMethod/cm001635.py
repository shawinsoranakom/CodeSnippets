def add_block(self, x, path=""):
        """adds all components inside a gradio block x to the registry of tracked components"""

        if hasattr(x, 'children'):
            if isinstance(x, gr.Tabs) and x.elem_id is not None:
                # Tabs element can't have a label, have to use elem_id instead
                self.add_component(f"{path}/Tabs@{x.elem_id}", x)
            for c in x.children:
                self.add_block(c, path)
        elif x.label is not None:
            self.add_component(f"{path}/{x.label}", x)
        elif isinstance(x, gr.Button) and x.value is not None:
            self.add_component(f"{path}/{x.value}", x)