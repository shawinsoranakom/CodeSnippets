def setUp(self):
        self.old_serializers = serializers._serializers
        serializers._serializers = {}