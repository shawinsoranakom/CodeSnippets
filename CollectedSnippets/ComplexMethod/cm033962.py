def _needs_debugger(task: Task, utr: _task.UnifiedTaskResult, globally_enabled: bool = False) -> bool:
    ignore_errors: bool = constants.config.get_config_value('TASK_DEBUGGER_IGNORE_ERRORS') and utr.ignore_errors
    ret = globally_enabled and ((utr.failed and not ignore_errors) or bool(utr.unreachable))

    match task.debugger:
        case 'always':
            ret = True
        case 'never':
            ret = False
        case 'on_failed' if utr.failed and not ignore_errors:
            ret = True
        case 'on_unreachable' if utr.unreachable:
            ret = True
        case 'on_skipped' if utr.skipped:
            ret = True

    return ret