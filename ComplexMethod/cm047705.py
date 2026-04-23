def enter_directive(self, directive, attrib, xpath):
        execution_context = None
        if self.execution_context_enabled:
            directive_info = {}
            if ('t-' + directive) in attrib:
                directive_info['t-' + directive] = repr(attrib['t-' + directive])
            if directive == 'set':
                if 't-value' in attrib:
                    directive_info['t-value'] = repr(attrib['t-value'])
                if 't-valuef' in attrib:
                    directive_info['t-valuef'] = repr(attrib['t-valuef'])

                for key in attrib:
                    if key.startswith('t-set-') or key.startswith('t-setf-'):
                        directive_info[key] = repr(attrib[key])
            elif directive == 'foreach':
                directive_info['t-as'] = repr(attrib['t-as'])
            elif directive == 'groups' and 'groups' in attrib and not directive_info.get('t-groups'):
                directive_info['t-groups'] = repr(attrib['groups'])
            elif directive == 'att':
                for key in attrib:
                    if key.startswith('t-att-') or key.startswith('t-attf-'):
                        directive_info[key] = repr(attrib[key])
            elif directive == 'options':
                for key in attrib:
                    if key.startswith('t-options-'):
                        directive_info[key] = repr(attrib[key])
            elif ('t-' + directive) not in attrib:
                directive_info['t-' + directive] = None

            execution_context = tools.profiler.ExecutionContext(**directive_info, xpath=xpath)
            execution_context.__enter__()
            self.context_stack.append(execution_context)

        for hook in self.qweb_hooks:
            hook('enter', self.cr.sql_log_count, view_id=self.view_id, xpath=xpath, directive=directive, attrib=attrib)