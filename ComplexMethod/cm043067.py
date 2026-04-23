def get_summary(self) -> Dict[str, Any]:
        """Get a summary of hook execution"""
        total_hooks = len(self.execution_log)
        successful = sum(1 for log in self.execution_log if log['status'] == 'success')
        failed = sum(1 for log in self.execution_log if log['status'] == 'failed')
        timed_out = sum(1 for log in self.execution_log if log['status'] == 'timeout')

        return {
            'total_executions': total_hooks,
            'successful': successful,
            'failed': failed,
            'timed_out': timed_out,
            'success_rate': (successful / total_hooks * 100) if total_hooks > 0 else 0,
            'total_errors': len(self.errors)
        }