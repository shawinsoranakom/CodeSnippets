def _handleClassSetUp(self, test, result):
        previousClass = result._previousTestClass
        currentClass = test.__class__
        if currentClass == previousClass:
            return
        if result._moduleSetUpFailed:
            return
        if currentClass.__unittest_skip__:
            return

        currentClass._classSetupFailed = False

        try:
            currentClass.setUpClass()
        except Exception as e:
            currentClass._classSetupFailed = True
            className = util.strclass(currentClass)
            self._createClassOrModuleLevelException(result, e,
                                                    'setUpClass',
                                                    className)
        finally:
            if currentClass._classSetupFailed is True:
                currentClass.doClassCleanups()
                if len(currentClass.tearDown_exceptions) > 0:
                    for exc in currentClass.tearDown_exceptions:
                        self._createClassOrModuleLevelException(
                                result, exc[1], 'setUpClass', className,
                                info=exc)