def shell_aliases(self):
        os.environ['TF_SHELL_ALIASES'] = (
            'fuck=\'eval $(thefuck $(fc -ln -1 | tail -n 1))\'\n'
            'l=\'ls -CF\'\n'
            'la=\'ls -A\'\n'
            'll=\'ls -alF\'')