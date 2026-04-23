def _tearDownPreviousClass(self, test, result):
        previousClass = result._previousTestClass
        currentClass = test.__class__
        if currentClass == previousClass:
            return
        if not previousClass:
            return
        if previousClass._classSetupFailed:
            return
        if previousClass.__unittest_skip__:
            return
        try:
            previousClass.tearDownClass()
        except Exception as e:
            className = util.strclass(previousClass)
            self._createClassOrModuleLevelException(result, e,
                                                    'tearDownClass',
                                                    className)
        finally:
            previousClass.doClassCleanups()
            if len(previousClass.tearDown_exceptions) > 0:
                for exc in previousClass.tearDown_exceptions:
                    className = util.strclass(previousClass)
                    self._createClassOrModuleLevelException(result, exc[1],
                                                            'tearDownClass',
                                                            className,
                                                            info=exc)