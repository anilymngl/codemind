"""Load testing script for evaluating Gradio 5.x queue behavior and concurrency handling."""
import asyncio
import time
import logging
from gradio_client import Client
from typing import List, Dict, Any
import statistics
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class QueueLoadTester:
    def __init__(self, api_url: str = "http://127.0.0.1:7860"):
        """Initialize load tester with API URL."""
        self.api_url = api_url
        self.results: List[Dict[str, Any]] = []
        
    async def send_request(
        self,
        request_id: int,
        endpoint: str,
        data: Any,
        test_name: str
    ) -> Dict[str, Any]:
        """Send a single request and measure timing."""
        client = Client(self.api_url)
        start_time = time.time()
        queue_time = None
        processing_time = None
        
        try:
            logger.info(f"[{test_name}] Request {request_id}: Starting")
            
            # Record queue entry time
            queue_start = time.time()
            
            # Use fn_index to target the correct wrapper function
            if endpoint == "query":
                result = await client.predict(str(data), fn_index=1)  # Query API wrapper
            else:
                result = await client.predict(str(data), fn_index=2)  # Sandbox API wrapper
            
            duration = (time.time() - start_time) * 1000
            
            logger.info(f"[{test_name}] Request {request_id}: Completed in {duration:.2f}ms")
            return {
                'request_id': request_id,
                'test_name': test_name,
                'success': True,
                'duration_ms': duration,
                'error': None,
                'queue_time_ms': queue_time,
                'processing_time_ms': processing_time
            }
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            logger.error(f"[{test_name}] Request {request_id}: Failed - {str(e)}")
            return {
                'request_id': request_id,
                'test_name': test_name,
                'success': False,
                'duration_ms': duration,
                'error': str(e),
                'queue_time_ms': queue_time,
                'processing_time_ms': None
            }
    
    async def run_concurrent_test(
        self,
        test_name: str,
        num_requests: int,
        concurrency: int,
        endpoint: str = "query",  # Remove leading slash
        data: Any = "Write a simple hello world program in Python",
        delay_between_batches_ms: int = 0
    ) -> Dict[str, Any]:
        """Run concurrent requests and collect metrics."""
        logger.info(f"Starting load test '{test_name}' with {num_requests} requests, concurrency={concurrency}")
        start_time = time.time()
        
        # Create tasks in batches based on concurrency
        all_results = []
        for batch_start in range(0, num_requests, concurrency):
            batch_size = min(concurrency, num_requests - batch_start)
            tasks = [
                self.send_request(
                    i + batch_start,
                    endpoint,
                    data,
                    test_name
                )
                for i in range(batch_size)
            ]
            batch_results = await asyncio.gather(*tasks)
            all_results.extend(batch_results)
            
            if delay_between_batches_ms > 0 and batch_start + concurrency < num_requests:
                await asyncio.sleep(delay_between_batches_ms / 1000)
        
        total_duration = (time.time() - start_time) * 1000
        successful_requests = [r for r in all_results if r['success']]
        failed_requests = [r for r in all_results if not r['success']]
        
        if successful_requests:
            durations = [r['duration_ms'] for r in successful_requests]
            queue_times = [r['queue_time_ms'] for r in successful_requests if r['queue_time_ms'] is not None]
            processing_times = [r['processing_time_ms'] for r in successful_requests if r['processing_time_ms'] is not None]
            
            metrics = {
                'test_name': test_name,
                'total_requests': num_requests,
                'concurrency': concurrency,
                'successful_requests': len(successful_requests),
                'failed_requests': len(failed_requests),
                'total_duration_ms': total_duration,
                'avg_duration_ms': statistics.mean(durations),
                'p50_duration_ms': statistics.median(durations),
                'p95_duration_ms': statistics.quantiles(durations, n=20)[18],
                'p99_duration_ms': statistics.quantiles(durations, n=100)[98],
                'min_duration_ms': min(durations),
                'max_duration_ms': max(durations),
                'throughput_rps': (len(successful_requests) / total_duration) * 1000,
                'error_rate': len(failed_requests) / num_requests
            }
            
            # Add queue metrics if available
            if queue_times:
                metrics.update({
                    'avg_queue_time_ms': statistics.mean(queue_times),
                    'p95_queue_time_ms': statistics.quantiles(queue_times, n=20)[18]
                })
            
            # Add processing metrics if available
            if processing_times:
                metrics.update({
                    'avg_processing_time_ms': statistics.mean(processing_times),
                    'p95_processing_time_ms': statistics.quantiles(processing_times, n=20)[18]
                })
        else:
            metrics = {
                'test_name': test_name,
                'total_requests': num_requests,
                'concurrency': concurrency,
                'successful_requests': 0,
                'failed_requests': len(failed_requests),
                'total_duration_ms': total_duration,
                'error_rate': 1.0,
                'throughput_rps': 0
            }
        
        # Log results
        logger.info(f"\nTest '{test_name}' completed:")
        logger.info(json.dumps(metrics, indent=2))
        
        return metrics

async def main():
    """Run a comprehensive series of load tests."""
    tester = QueueLoadTester()
    
    # Test configurations
    test_scenarios = [
        # Baseline tests
        {
            'name': 'baseline_single',
            'requests': 5,
            'concurrency': 1,
            'endpoint': 'query',  # Remove leading slash
            'delay_ms': 0
        },
        # Concurrency tests
        {
            'name': 'concurrency_limit',
            'requests': 10,
            'concurrency': 3,  # Matches our configured limit
            'endpoint': 'query',  # Remove leading slash
            'delay_ms': 0
        },
        # Over concurrency tests
        {
            'name': 'over_concurrency',
            'requests': 15,
            'concurrency': 5,  # Above our configured limit
            'endpoint': 'query',  # Remove leading slash
            'delay_ms': 0
        },
        # Queue size tests
        {
            'name': 'queue_size_limit',
            'requests': 25,
            'concurrency': 3,
            'endpoint': 'query',  # Remove leading slash
            'delay_ms': 0
        },
        # Mixed workload
        {
            'name': 'mixed_endpoints',
            'requests': 10,
            'concurrency': 2,
            'endpoint': 'run_sandbox',  # Remove leading slash
            'data': 'print("Hello, World!")',
            'delay_ms': 100
        }
    ]
    
    results = []
    for scenario in test_scenarios:
        logger.info(f"\nRunning test scenario: {scenario['name']}")
        metrics = await tester.run_concurrent_test(
            test_name=scenario['name'],
            num_requests=scenario['requests'],
            concurrency=scenario['concurrency'],
            endpoint=scenario.get('endpoint', 'query'),  # Remove leading slash
            data=scenario.get('data', "Write a simple hello world program in Python"),
            delay_between_batches_ms=scenario.get('delay_ms', 0)
        )
        results.append(metrics)
        # Wait between test scenarios
        await asyncio.sleep(2)
    
    # Generate summary report
    logger.info("\n=== Load Test Summary ===")
    for metrics in results:
        logger.info(f"\nTest: {metrics['test_name']}")
        logger.info(f"Concurrency: {metrics['concurrency']}")
        logger.info(f"Success Rate: {((1 - metrics['error_rate']) * 100):.1f}%")
        logger.info(f"Throughput: {metrics['throughput_rps']:.2f} req/s")
        if 'avg_duration_ms' in metrics:
            logger.info(f"Avg Duration: {metrics['avg_duration_ms']:.2f}ms")
            logger.info(f"P95 Duration: {metrics['p95_duration_ms']:.2f}ms")
        if 'avg_queue_time_ms' in metrics:
            logger.info(f"Avg Queue Time: {metrics['avg_queue_time_ms']:.2f}ms")
        
    # Save results to file
    with open('load_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    logger.info("\nDetailed results saved to load_test_results.json")

if __name__ == "__main__":
    asyncio.run(main()) 