import asyncio
import httpx
import time
import sys
import os

SERVER_URL = "http://localhost:8080"

TEST_DURATION_SECONDS = 5 
CONNECTION_TIMEOUT = 10.0

async def run_client_test(rate_rps: int):
    total_requests_to_send = rate_rps * TEST_DURATION_SECONDS
    inter_request_delay = 1.0 / rate_rps
    
    print(f"Starting Test")
    print(f"Target Rate: {rate_rps} RPS (total {total_requests_to_send} requests over {TEST_DURATION_SECONDS}s)")
    print(f"Server Target: {SERVER_URL}")

    tasks = []
    
    async with httpx.AsyncClient(timeout=CONNECTION_TIMEOUT) as client:
        
        start_time = time.perf_counter()
        
        for _ in range(total_requests_to_send):
            task = asyncio.create_task(client.get(SERVER_URL))
            tasks.append(task)

            await asyncio.sleep(inter_request_delay)
            
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.perf_counter()
        duration = end_time - start_time
        
    successful_requests = sum(1 for r in responses if isinstance(r, httpx.Response) and r.status_code == 200)
    rate_limited_requests = sum(1 for r in responses if isinstance(r, httpx.Response) and r.status_code == 429)

    print(f"\nResults for {rate_rps} RPS Test")
    print(f"Total time elapsed: {duration:.4f} seconds")
    print(f"Successful requests (200 OK): {successful_requests}")
    print(f"Rate-limited requests (429 Too Many Requests): {rate_limited_requests}")
    
    if duration > 0:
        throughput = successful_requests / duration
        print(f"Successful Throughput (Average): {throughput:.2f} requests/second")

def main():
    if len(sys.argv) != 2:
        print(f"Usage: python {os.path.basename(sys.argv[0])} <REQUESTS_PER_SECOND>")
        print("\nExample: python rps_client.py 10")
        sys.exit(1)
    
    try:
        rate_rps = int(sys.argv[1])
        if rate_rps <= 0:
            raise ValueError("RPS must be a positive integer.")
    except ValueError as e:
        print(f"Error: Invalid RPS value. {e}")
        sys.exit(1)

    try:
        asyncio.run(run_client_test(rate_rps))
    except ConnectionRefusedError:
        print(f"\n[ERROR] Connection Refused. Please ensure your Multithreaded Server is running on {SERVER_URL}.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
