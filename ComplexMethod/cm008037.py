def process_color_policy(stream):
            stream_name = {sys.stdout: 'stdout', sys.stderr: 'stderr'}[stream]
            policy = traverse_obj(self.params, ('color', (stream_name, None), {str}, any)) or 'auto'
            if policy in ('auto', 'auto-tty', 'no_color-tty'):
                no_color = base_no_color
                if policy.endswith('tty'):
                    no_color = policy.startswith('no_color')
                if term_allow_color and supports_terminal_sequences(stream):
                    return 'no_color' if no_color else True
                return False
            assert policy in ('always', 'never', 'no_color'), policy
            return {'always': True, 'never': False}.get(policy, policy)