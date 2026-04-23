def _check_progress_bar(self, node):
        if any('o_progressbar' in node.get(cl, '') for cl in att_names('class')):
            if node.get('role') != 'progressbar':
                msg = 'o_progressbar class must have progressbar role'
                self._log_view_warning(msg, node)
            if not any(node.get(at) for at in att_names('aria-valuenow')):
                msg = 'o_progressbar class must have aria-valuenow attribute'
                self._log_view_warning(msg, node)
            if not any(node.get(at) for at in att_names('aria-valuemin')):
                msg = 'o_progressbar class must have aria-valuemin attribute'
                self._log_view_warning(msg, node)
            if not any(node.get(at) for at in att_names('aria-valuemax')):
                msg = 'o_progressbar class must have aria-valuemaxattribute'
                self._log_view_warning(msg, node)