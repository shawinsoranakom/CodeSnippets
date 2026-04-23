def get_appwise_nodes(self,node:Control) -> tuple[list[TreeElementNode],list[TextElementNode]]:
        all_apps=node.GetChildren()
        visible_apps = {app.Name: app for app in all_apps if self.desktop.is_app_visible(app) and app.Name not in AVOIDED_APPS}
        apps={'Taskbar':visible_apps.pop('Taskbar'),'Program Manager':visible_apps.pop('Program Manager')}
        if visible_apps:
            foreground_app = list(visible_apps.values()).pop(0)
            apps[foreground_app.Name.strip()]=foreground_app
        interactive_nodes,informative_nodes,scrollable_nodes=[],[],[]
        # Parallel traversal (using ThreadPoolExecutor) to get nodes from each app
        with ThreadPoolExecutor() as executor:
            future_to_node = {executor.submit(self.get_nodes, app): app for app in apps.values()}
            for future in as_completed(future_to_node):
                try:
                    result = future.result()
                    if result:
                        element_nodes,text_nodes,scroll_nodes=result
                        interactive_nodes.extend(element_nodes)
                        informative_nodes.extend(text_nodes)
                        scrollable_nodes.extend(scroll_nodes)
                except Exception as e:
                    print(f"Error processing node {future_to_node[future].Name}: {e}")
        return interactive_nodes,informative_nodes,scrollable_nodes