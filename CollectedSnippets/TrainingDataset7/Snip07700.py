def __init__(self, inclusive_lower=True, inclusive_upper=False):
        self.lower = "[" if inclusive_lower else "("
        self.upper = "]" if inclusive_upper else ")"