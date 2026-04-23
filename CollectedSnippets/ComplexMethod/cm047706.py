def _get_directive_profiling_name(self, directive, attrib):
        expr = ''
        if directive == 'set':
            if 't-set' in attrib:
                expr = f"t-set={repr(attrib['t-set'])}"
                if 't-value' in attrib:
                    expr += f" t-value={repr(attrib['t-value'])}"
                if 't-valuef' in attrib:
                    expr += f" t-valuef={repr(attrib['t-valuef'])}"
            for key in attrib:
                if key.startswith('t-set-') or key.startswith('t-setf-'):
                    if expr:
                        expr += ' '
                    expr += f"{key}={repr(attrib[key])}"
        elif directive == 'foreach':
            expr = f"t-foreach={repr(attrib['t-foreach'])} t-as={repr(attrib['t-as'])}"
        elif directive == 'options':
            if attrib.get('t-options'):
                expr = f"t-options={repr(attrib['t-options'])}"
            for key in attrib:
                if key.startswith('t-options-'):
                    expr = f"{expr}  {key}={repr(attrib[key])}"
        elif directive == 'att':
            for key in attrib:
                if key == 't-att' or key.startswith('t-att-') or key.startswith('t-attf-'):
                    if expr:
                        expr += ' '
                    expr += f"{key}={repr(attrib[key])}"
        elif ('t-' + directive) in attrib:
            expr = f"t-{directive}={repr(attrib['t-' + directive])}"
        else:
            expr = f"t-{directive}"

        return expr