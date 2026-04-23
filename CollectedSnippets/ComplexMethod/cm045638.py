def test_python_subject_deletions_enabled_defaults():
    class SimpleSubject(pw.io.python.ConnectorSubject):

        def run(self):
            self.next_json({"a": 10})
            self.next_json({"b": 50})

    assert not SimpleSubject()._deletions_enabled

    class SimpleSubjectExplicitRemovals(pw.io.python.ConnectorSubject):

        def run(self):
            self.next_json({"a": 10})
            self.next_json({"b": 50})
            self._remove(None, json.dumps({"a": 10}))

    assert SimpleSubjectExplicitRemovals()._deletions_enabled

    class SimpleSubjectImplicitRemovals(pw.io.python.ConnectorSubject):

        def run(self):
            self.a()

        def a(self):
            self._buffer.put((pw.io.python.PythonConnectorEventType.DELETE, None, None))

    assert SimpleSubjectImplicitRemovals()._deletions_enabled

    class SimpleSubjectLowLevelNoRemovals(pw.io.python.ConnectorSubject):

        def run(self):
            self._buffer.put((pw.io.python.PythonConnectorEventType.INSERT, None, None))
            self._buffer.put(
                (pw.io.python.PythonConnectorEventType.EXTERNAL_OFFSET, None, None)
            )

    assert not SimpleSubjectLowLevelNoRemovals()._deletions_enabled

    class SimpleSubjectWithCondition(pw.io.python.ConnectorSubject):

        def run(self):
            if random.choice([True, False]):
                self._insert(None, json.dumps({"a": 10}))
            else:
                self._remove(None, json.dumps({"a": 10}))

    assert SimpleSubjectWithCondition()._deletions_enabled

    class SimpleSubjectDeletionUnreachable(pw.io.python.ConnectorSubject):

        def run(self):
            self.next_json({"a": 10})

        def delete_something(self):
            self._remove(None, json.dumps({"a": 10}))

    assert not SimpleSubjectDeletionUnreachable()._deletions_enabled

    class SimpleSubjectWontParse(pw.io.python.ConnectorSubject):

        def run(self):
            self.__str__()

    assert not SimpleSubjectWontParse()._deletions_enabled

    assert not pw.io.python._are_deletions_reachable(str)