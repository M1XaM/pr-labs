import asyncio
import time
import httpx
from typing import Dict, Any

OPTIONS = {
    'CONCURRENT': "http://localhost:8080",
    'SINGLE_THREAD': "http://localhost:8081"
}
TARGET_SERVER = OPTIONS['SINGLE_THREAD']

NUM_REQUESTS = 10
SIMULATED_DELAY_SECONDS = 1.0
TIMEOUT_SECONDS = (NUM_REQUESTS * SIMULATED_DELAY_SECONDS) + 5.0

async def make_request(client: httpx.AsyncClient, url: str, index: int) -> Dict[str, Any]:
    start_time = time.perf_counter()
    try:
        response = await client.get(url)
        response.raise_for_status() 
        end_time = time.perf_counter()
        
        return {
            "index": index,
            "status": response.status_code,
            "duration": end_time - start_time,
            "success": True
        }
    except httpx.HTTPStatusError as e:
        print(f"Request {index} failed with HTTP error: {e}")
        return {"index": index, "success": False, "error": str(e)}
    except httpx.RequestError as e:
        print(f"Request {index} failed with connection error: {e}")
        return {"index": index, "success": False, "error": str(e)}

async def run_test(url: str):
    print(f"Target URL: {url}")
    
    start_total_time = time.perf_counter()
    
    async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
        tasks = [make_request(client, url, i + 1) for i in range(NUM_REQUESTS)]
        results = await asyncio.gather(*tasks)

    end_total_time = time.perf_counter()
    total_time = end_total_time - start_total_time

    successful_requests = sum(1 for r in results if r["success"])
    print("\nTest Summary:")
    print(f"Total requests attempted: {NUM_REQUESTS}")
    print(f"Successful requests: {successful_requests}")
    print(f"Total time execution: {total_time:.4f} seconds")
    
if __name__ == "__main__":
    asyncio.run(run_test(TARGET_SERVER))
