def print_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)

        total = len(self.results)
        passed = sum(1 for r in self.results if r['status'] == 'PASS')
        failed = sum(1 for r in self.results if r['status'] == 'FAIL')

        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success Rate: {(passed/total)*100:.1f}%")

        if failed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.results:
                if result['status'] == 'FAIL':
                    print(f"  • {result['method']} {result['endpoint']}")
                    if 'error' in result:
                        print(f"    Error: {result['error']}")

        # Performance statistics
        response_times = [r['response_time'] for r in self.results if r['response_time'] > 0]
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)
            print(f"\n⏱️  Average Response Time: {avg_time:.3f}s")
            print(f"⏱️  Max Response Time: {max_time:.3f}s")

        # Save detailed report
        report_file = f"crawl4ai_test_report_{int(time.time())}.json"
        with open(report_file, 'w') as f:
            json.dump({
                "timestamp": time.time(),
                "server_url": self.base_url,
                "version": "0.7.0",
                "summary": {
                    "total": total,
                    "passed": passed,
                    "failed": failed
                },
                "results": self.results
            }, f, indent=2)

        print(f"\n📄 Detailed report saved to: {report_file}")