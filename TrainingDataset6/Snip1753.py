def __init__(self):
        self._parser = ArgumentParser(prog='thefuck', add_help=False)
        self._add_arguments()