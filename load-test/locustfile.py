"""
Locust Load Test for Smart CDN
Simulates user traffic to test AI-enabled vs baseline caching performance
"""
from locust import HttpUser, task, between
import random
import json


class CDNUser(HttpUser):
    """
    Simulates a user browsing content through the CDN.
    """
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    
    def on_start(self):
        """Called when a user starts"""
        # Get list of available edges and content
        self.edges = ["edge-us-east-1", "edge-us-west-1", "edge-eu-west-1"]
        self.content_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]  # Common content IDs
        
    @task(3)
    def request_content(self):
        """
        Request content from an edge node (most common task).
        This simulates a cache hit or miss scenario.
        """
        edge_id = random.choice(self.edges)
        content_id = random.choice(self.content_ids)
        
        # Simulate request to edge simulator
        # In a real scenario, this would go through the edge node
        # For testing, we'll call the edge simulator directly
        with self.client.get(
            f"/edge/{edge_id}/content/{content_id}",
            catch_response=True,
            name="Request Content"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                response.failure("Content not found")
            else:
                response.failure(f"Unexpected status: {response.status_code}")
    
    @task(1)
    def request_popular_content(self):
        """
        Request popular content (higher probability of cache hit).
        """
        edge_id = random.choice(self.edges)
        # Popular content IDs (1-3)
        content_id = random.choice([1, 2, 3])
        
        with self.client.get(
            f"/edge/{edge_id}/content/{content_id}",
            catch_response=True,
            name="Request Popular Content"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")
    
    @task(1)
    def request_rare_content(self):
        """
        Request rare content (higher probability of cache miss).
        """
        edge_id = random.choice(self.edges)
        # Rare content IDs (8-10)
        content_id = random.choice([8, 9, 10])
        
        with self.client.get(
            f"/edge/{edge_id}/content/{content_id}",
            catch_response=True,
            name="Request Rare Content"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")


class EdgeSimulatorUser(HttpUser):
    """
    Simulates requests directly to the edge simulator API.
    This is more realistic for testing the full CDN stack.
    """
    wait_time = between(0.5, 2)  # Faster requests for edge simulator
    
    def on_start(self):
        """Called when a user starts"""
        self.edges = ["edge-us-east-1", "edge-us-west-1", "edge-eu-west-1"]
        self.content_ids = list(range(1, 11))
        
    @task(5)
    def simulate_edge_request(self):
        """
        Simulate a request through the edge simulator.
        This will trigger cache lookup, origin fetch if needed, and metrics logging.
        """
        edge_id = random.choice(self.edges)
        content_id = random.choice(self.content_ids)
        
        # Request through edge simulator
        with self.client.get(
            f"/edge/{edge_id}/content/{content_id}",
            catch_response=True,
            name="Edge Request"
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")
    
    @task(1)
    def trigger_ai_decisions(self):
        """
        Trigger AI decision generation (less frequent).
        """
        with self.client.post(
            "/api/v1/ai/decide",
            params={"time_window_minutes": 60, "apply_decisions": True},
            catch_response=True,
            name="Trigger AI Decisions"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")


class SpikeTestUser(HttpUser):
    """
    Simulates traffic spikes (viral content scenario).
    Use this for spike testing.
    """
    wait_time = between(0.1, 0.5)  # Very fast requests during spike
    
    def on_start(self):
        """Called when a user starts"""
        self.edges = ["edge-us-east-1", "edge-us-west-1", "edge-eu-west-1"]
        # Viral content ID (most requested during spike)
        self.viral_content_id = 1
        
    @task(10)
    def request_viral_content(self):
        """
        Request viral content repeatedly (simulates traffic spike).
        """
        edge_id = random.choice(self.edges)
        
        with self.client.get(
            f"/edge/{edge_id}/content/{self.viral_content_id}",
            catch_response=True,
            name="Viral Content Request"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")


# Configuration for different test scenarios
class NormalLoadTest(EdgeSimulatorUser):
    """Normal load test scenario"""
    pass


class SpikeLoadTest(SpikeTestUser):
    """Spike load test scenario"""
    pass
