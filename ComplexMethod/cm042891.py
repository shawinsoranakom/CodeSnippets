def get_report(self) -> Dict:
        if not self.memory_samples: return {"error": "No memory samples collected"}
        total_time = time.time() - self.start_time; valid_samples = [s['memory_mb'] for s in self.memory_samples if s['memory_mb'] is not None]
        start_mem = valid_samples[0] if valid_samples else None; end_mem = valid_samples[-1] if valid_samples else None
        max_mem = max(valid_samples) if valid_samples else None; avg_mem = sum(valid_samples) / len(valid_samples) if valid_samples else None
        growth = (end_mem - start_mem) if start_mem is not None and end_mem is not None else None
        return {"test_id": self.test_id, "total_time_seconds": total_time, "sample_count": len(self.memory_samples), "valid_sample_count": len(valid_samples), "csv_path": str(self.csv_path), "platform": sys.platform, "start_memory_mb": start_mem, "end_memory_mb": end_mem, "max_memory_mb": max_mem, "average_memory_mb": avg_mem, "memory_growth_mb": growth}