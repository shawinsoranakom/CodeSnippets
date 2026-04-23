def __init__(self, obj, m2m_data=None, deferred_fields=None):
        self.object = obj
        self.m2m_data = m2m_data
        self.deferred_fields = deferred_fields