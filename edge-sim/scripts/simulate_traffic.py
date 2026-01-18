"""
Traffic Simulation Script
Generates requests to edge simulator to test cache behavior
"""
import asyncio
import httpx
import random
import time
import argparse
from typing import List

# Edge simulator URL
EDGE_SIM_URL = "http://localhost:8002"

# Default content IDs for simulation
DEFAULT_CONTENT_IDS = [
    1,2,3
]

# Edge IDs
EDGE_IDS = ["edge-us-east", "edge-us-west", "edge-eu-west"]


async def make_request(
    client: httpx.AsyncClient,
    content_id: str,
    edge_id: str,
    verbose: bool = False
) -> dict:
    """Make a single request to edge simulator"""
    try:
        start_time = time.time()
        response = await client.get(
            f"{EDGE_SIM_URL}/api/v1/content/{content_id}",
            headers={"X-Edge-Id": edge_id},
            timeout=10.0
        )
        elapsed = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            data = response.json()
            result = {
                "content_id": content_id,
                "edge_id": edge_id,
                "cache_hit": data.get("is_cache_hit", False),
                "response_time_ms": data.get("response_time_ms", 0),
                "status": "success"
            }
            if verbose:
                print(f"✓ {content_id} @ {edge_id}: {'HIT' if result['cache_hit'] else 'MISS'} ({result['response_time_ms']}ms)")
            return result
        else:
            result = {
                "content_id": content_id,
                "edge_id": edge_id,
                "status": "error",
                "status_code": response.status_code
            }
            if verbose:
                print(f"✗ {content_id} @ {edge_id}: Error {response.status_code}")
            return result
    except Exception as e:
        result = {
            "content_id": content_id,
            "edge_id": edge_id,
            "status": "error",
            "error": str(e)
        }
        if verbose:
            print(f"✗ {content_id} @ {edge_id}: {e}")
        return result


async def simulate_traffic(
    num_requests: int = 100,
    content_ids: List[str] = None,
    edge_ids: List[str] = None,
    delay_ms: int = 100,
    verbose: bool = False
):
    """
    Simulate CDN traffic.
    
    Args:
        num_requests: Number of requests to make
        content_ids: List of content IDs (defaults to DEFAULT_CONTENT_IDS)
        edge_ids: List of edge IDs (defaults to EDGE_IDS)
        delay_ms: Delay between requests in milliseconds
        verbose: Print each request result
    """
    if content_ids is None:
        content_ids = DEFAULT_CONTENT_IDS
    if edge_ids is None:
        edge_ids = EDGE_IDS
    
    print(f"Starting traffic simulation:")
    print(f"  Requests: {num_requests}")
    print(f"  Content IDs: {len(content_ids)}")
    print(f"  Edge IDs: {len(edge_ids)}")
    print(f"  Delay: {delay_ms}ms between requests")
    print()
    
    client = httpx.AsyncClient()
    
    hits = 0
    misses = 0
    errors = 0
    total_response_time = 0
    
    try:
        for i in range(num_requests):
            content_id = random.choice(content_ids)
            edge_id = random.choice(edge_ids)
            
            result = await make_request(client, content_id, edge_id, verbose)
            
            if result.get("status") == "success":
                if result.get("cache_hit"):
                    hits += 1
                else:
                    misses += 1
                total_response_time += result.get("response_time_ms", 0)
            else:
                errors += 1
            
            # Delay between requests
            if delay_ms > 0 and i < num_requests - 1:
                await asyncio.sleep(delay_ms / 1000.0)
            
            # Progress update
            if not verbose and (i + 1) % 10 == 0:
                print(f"Progress: {i + 1}/{num_requests} requests")
        
        # Print summary
        print()
        print("=" * 50)
        print("Simulation Summary")
        print("=" * 50)
        print(f"Total requests: {num_requests}")
        print(f"Cache hits: {hits} ({hits/num_requests*100:.1f}%)")
        print(f"Cache misses: {misses} ({misses/num_requests*100:.1f}%)")
        print(f"Errors: {errors}")
        if hits + misses > 0:
            avg_response_time = total_response_time / (hits + misses)
            print(f"Average response time: {avg_response_time:.2f}ms")
        print("=" * 50)
        
    finally:
        await client.aclose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulate CDN traffic")
    parser.add_argument("-n", "--num-requests", type=int, default=100, help="Number of requests")
    parser.add_argument("-d", "--delay", type=int, default=100, help="Delay between requests (ms)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--content-ids", nargs="+", help="Content IDs to request")
    parser.add_argument("--edge-ids", nargs="+", help="Edge IDs to use")
    
    args = parser.parse_args()
    
    asyncio.run(simulate_traffic(
        num_requests=args.num_requests,
        content_ids=args.content_ids,
        edge_ids=args.edge_ids,
        delay_ms=args.delay,
        verbose=args.verbose
    ))
