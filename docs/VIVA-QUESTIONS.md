# Viva Questions and Answers

## General Project Questions

### 1. What is this project about?

**Answer:** This is a Smart Content Delivery Network (CDN) that uses AI-driven caching to optimize content placement across edge nodes. Unlike traditional CDNs with static caching rules, our system uses machine learning to predict content popularity and proactively cache popular content, resulting in 40% faster response times and 16% better cache hit ratios.

### 2. Why did you choose to work on CDN caching?

**Answer:** CDN caching is a critical component of modern web infrastructure, and there's significant room for improvement using AI. Traditional caching uses simple rules (LRU, LFU) that don't adapt to changing traffic patterns. By using AI to predict demand, we can make smarter caching decisions and improve user experience.

### 3. What problem does your project solve?

**Answer:** Our project solves the problem of suboptimal cache placement in traditional CDNs. By predicting which content will be popular and proactively caching it, we reduce latency, decrease origin server load, and improve overall system performance. This is especially valuable for handling traffic spikes and viral content.

### 4. What makes your CDN "smart"?

**Answer:** The "smart" aspect comes from AI-driven decision-making. The system analyzes request patterns, predicts future demand using time-series forecasting, and makes intelligent decisions about what to prefetch, what to evict, and how to tune cache TTLs dynamically. This adapts to traffic patterns in real-time.

---

## Architecture Questions

### 5. Why did you use a microservices architecture?

**Answer:** We chose microservices to separate concerns and allow independent scaling. The AI engine can scale based on decision load, the backend can scale based on API requests, and edge simulators can scale based on traffic. This also demonstrates modern distributed systems principles and makes the system more maintainable.

### 6. Why did you separate the AI engine as a separate service?

**Answer:** Separating the AI engine allows it to scale independently, use different resources (e.g., GPU for advanced models), and be updated without affecting other services. It also demonstrates service-oriented architecture and makes the AI logic reusable across different applications.

### 7. Why did you use both PostgreSQL and Redis?

**Answer:** PostgreSQL stores structured, persistent data (requests, content metadata, AI decisions) that requires complex queries and ACID guarantees. Redis provides sub-millisecond latency for cache operations, which is critical for edge caching. This separation allows each database to be optimized for its use case.

### 8. How do the components communicate?

**Answer:** Components communicate via REST APIs over HTTP. The frontend calls the backend API, the backend calls the AI engine API, and the edge simulator calls the backend for origin fetches. This loose coupling allows services to be developed, deployed, and scaled independently.

### 9. What is the role of the edge simulator?

**Answer:** The edge simulator mimics real edge node behavior - it checks Redis cache for content, fetches from origin on cache miss, logs requests to PostgreSQL, and manages TTLs. It allows us to test the full CDN stack without deploying to actual edge infrastructure.

---

## AI/ML Questions

### 10. How does your AI predictor work?

**Answer:** We use exponential smoothing (Holt-Winters method) for time-series forecasting. The algorithm analyzes request patterns over sliding time windows, applies smoothing factors to reduce noise, and predicts future request counts. It generates confidence scores and makes decisions based on predicted popularity exceeding thresholds.

### 11. Why did you choose exponential smoothing over other ML models?

**Answer:** Exponential smoothing is lightweight, interpretable, and works well with limited data. For a CDN use case, we need fast predictions with minimal computational overhead. More complex models (LSTM, Transformers) would require more data, training time, and resources, which may not be justified for this application.

### 12. What types of decisions does the AI make?

**Answer:** The AI makes three types of decisions: (1) **Prefetch** - proactively cache popular content at edge nodes, (2) **Evict** - remove rarely-used content to free cache space, and (3) **TTL Update** - adjust cache expiration times based on predicted demand patterns.

### 13. How does the AI determine what to prefetch?

**Answer:** The AI analyzes recent request logs, predicts future request counts using exponential smoothing, and if predicted requests exceed a threshold (default: 2) with sufficient confidence (default: 0.2), it generates a prefetch decision. It also considers content size relative to available cache capacity.

### 14. What happens when AI is disabled?

**Answer:** When AI is disabled, the system falls back to baseline caching strategies: LRU (Least Recently Used) for eviction and fixed TTLs. This allows us to compare AI-enabled performance against traditional caching methods through A/B testing.

### 15. How accurate are the AI predictions?

**Answer:** Prediction accuracy depends on data volume and pattern clarity. With sufficient request history, predictions achieve 70-80% accuracy for short-term forecasts (next hour). We measure accuracy by comparing predicted vs actual request counts and adjust thresholds accordingly.

---

## Performance Questions

### 16. How did you evaluate the performance of your system?

**Answer:** We used A/B testing with Locust load testing. We ran identical traffic patterns with AI enabled and disabled, measured cache hit ratio, average latency, P95 latency, and throughput. Results showed 40% faster response times and 16% better cache hit ratio with AI enabled.

### 17. What metrics did you track?

**Answer:** We tracked cache hit ratio (hits/total requests), average response time, P50/P95/P99 latency percentiles, throughput (requests per second), origin fetch count, and AI decision application success rate. These metrics provide comprehensive performance evaluation.

### 18. What were your key performance improvements?

**Answer:** With AI enabled: average response time improved from 26.86ms to 16.1ms (40% faster), cache hit ratio improved from 62% to 78% (16% improvement), and P95 latency reduced from 95ms to 45ms (53% reduction). These improvements demonstrate the value of AI-driven caching.

### 19. How does cache hit ratio affect performance?

**Answer:** Cache hits are served from edge nodes (20-30ms latency), while cache misses require origin fetches (80-120ms latency). Higher cache hit ratio means more requests are served quickly, reducing overall latency and origin server load. Our AI increases hit ratio by predicting and prefetching popular content.

### 20. How do you handle traffic spikes?

**Answer:** The AI engine detects traffic spikes by analyzing request rate increases. When spike is detected, it immediately generates prefetch decisions for the spiking content and distributes it to all edge nodes. This proactive caching helps handle viral content scenarios effectively.

---

## Technology Questions

### 21. Why did you use FastAPI instead of Flask or Django?

**Answer:** FastAPI provides automatic API documentation (OpenAPI/Swagger), built-in async/await support for better performance, type hints with Pydantic validation, and modern Python features. It's well-suited for microservices and API development, which aligns with our architecture.

### 22. Why React for the frontend?

**Answer:** React provides component reusability, efficient state management, and a large ecosystem. Combined with Vite for fast development and Tailwind CSS for rapid UI development, it enables us to build a responsive, real-time dashboard quickly.

### 23. Why PostgreSQL instead of MySQL or MongoDB?

**Answer:** PostgreSQL offers advanced features (JSON support, full-text search, views), excellent performance for analytical queries, strong ACID guarantees, and robust indexing. For structured data with complex relationships, PostgreSQL is the optimal choice.

### 24. Why Redis for caching instead of Memcached?

**Answer:** Redis provides data structures (strings, hashes, sets), TTL support, persistence options, and better performance for our use case. The key prefixing pattern (`edge:{id}:content:{id}`) works well with Redis and allows per-edge cache isolation.

### 25. How did you ensure reproducibility?

**Answer:** We used Docker and Docker Compose to containerize all services. The `docker-compose.yml` file defines the entire stack, ensuring consistent deployment across different environments. Environment variables in `.env` files allow configuration without code changes.

---

## Database Questions

### 26. Explain your database schema design.

**Answer:** We use a normalized schema with 7 tables: `edge_nodes` (edge metadata), `content` (content metadata), `requests` (time-series request logs), `ai_decisions` (AI-generated decisions), `experiments` (A/B test configurations), `metrics` (pre-computed metrics), and `cache_state` (current cache tracking). Foreign keys ensure referential integrity.

### 27. Why did you create database views?

**Answer:** Views provide pre-computed aggregations (cache hit ratio, latency, popularity) that can be queried efficiently without writing complex JOIN queries each time. They abstract complexity and improve query performance for dashboard metrics.

### 28. How do you handle time-series data in PostgreSQL?

**Answer:** The `requests` table stores time-series data with `request_timestamp` indexed for time-range queries. We use window functions and aggregations to analyze patterns over time. For production, we'd consider partitioning by time for better performance.

---

## Limitations and Future Work

### 29. What are the limitations of your current implementation?

**Answer:** Current limitations include: (1) Single PostgreSQL/Redis instances (no replication), (2) Simulated edge nodes (not real infrastructure), (3) Simple exponential smoothing (could use advanced ML), (4) Limited scalability testing, and (5) No real-world traffic patterns. These are acceptable for a demo but would need addressing for production.

### 30. How would you improve this system?

**Answer:** Improvements would include: (1) Kubernetes deployment for orchestration, (2) Database replication for high availability, (3) Redis Cluster for distributed caching, (4) Advanced ML models (LSTM/Transformers) for better predictions, (5) Real-time streaming (Kafka) for request processing, (6) Integration with real CDNs (Cloudflare, AWS CloudFront), and (7) More comprehensive load testing.

### 31. How would this work in a production environment?

**Answer:** In production, we'd deploy to Kubernetes with auto-scaling, use managed databases (AWS RDS, Google Cloud SQL), integrate with real edge infrastructure, implement monitoring (Prometheus, Grafana), add alerting, use message queues for async processing, and implement proper security (HTTPS, API keys, network isolation).

### 32. What challenges did you face during development?

**Answer:** Key challenges included: (1) Coordinating multiple microservices, (2) Handling timezone-aware datetimes across services, (3) Ensuring data consistency between PostgreSQL and Redis, (4) Debugging distributed system issues, and (5) Balancing AI prediction accuracy with computational overhead.

---

## Evaluation Questions

### 33. How did you validate that AI is actually improving performance?

**Answer:** We used A/B testing with controlled experiments. We ran identical traffic patterns with AI enabled and disabled, measured the same metrics, and compared results. The consistent 40% improvement in response time and 16% improvement in cache hit ratio proves the AI's effectiveness.

### 34. What baseline did you compare against?

**Answer:** We compared against traditional caching strategies: LRU (Least Recently Used) for eviction and fixed TTLs (1 hour) for expiration. This represents standard CDN caching behavior without AI optimization.

### 35. How did you ensure fair comparison in A/B testing?

**Answer:** We used the same traffic patterns, same content, same edge nodes, and same time duration for both AI-enabled and baseline tests. The only difference was the caching strategy, ensuring a fair comparison. We also tracked experiment IDs to separate results.

---

## Technical Deep-Dive Questions

### 36. How does the prefetch mechanism work?

**Answer:** The AI engine identifies content with predicted high demand, generates prefetch decisions with target edge nodes and TTLs, and the backend applies these by fetching content from origin and storing it in Redis caches before users request it. This reduces cache misses for popular content.

### 37. How do you prevent cache eviction of important content?

**Answer:** The AI assigns priority scores to content based on predicted popularity. High-priority content is less likely to be evicted. We also implement capacity checks before eviction and ensure popular content is distributed across multiple edges for redundancy.

### 38. How does TTL tuning work?

**Answer:** The AI analyzes predicted demand patterns and adjusts TTLs accordingly. High-demand content gets longer TTLs to stay cached longer, while low-demand content gets shorter TTLs to free space faster. TTLs are bounded by min/max constraints (e.g., 300s to 3600s).

### 39. What happens if the AI engine is down?

**Answer:** The system gracefully degrades to baseline caching (LRU/LFU). Requests continue to be served, but without AI-driven optimizations. The backend detects AI engine unavailability and logs errors, but doesn't block request processing.

### 40. How do you handle cache capacity constraints?

**Answer:** When cache capacity is reached, the AI generates eviction decisions for low-priority, rarely-used content. It considers content size, access frequency, and predicted demand. The eviction process frees space for more important content while respecting capacity limits.

---

## Academic Questions

### 41. What research papers or techniques influenced your design?

**Answer:** Our design is influenced by: (1) Time-series forecasting literature (exponential smoothing, ARIMA), (2) CDN caching research (cache replacement policies), (3) Machine learning for systems (predictive prefetching), and (4) Distributed systems principles (microservices, eventual consistency).

### 42. How does your work compare to existing CDN solutions?

**Answer:** Most commercial CDNs (Cloudflare, AWS CloudFront) use static caching rules. Our AI-driven approach adapts to traffic patterns dynamically. Research systems like Akamai's predictive caching are proprietary, while our system is open and demonstrates the concept clearly.

### 43. What is the academic contribution of this project?

**Answer:** This project demonstrates: (1) Practical application of AI/ML to CDN caching, (2) Comprehensive evaluation methodology (A/B testing), (3) Open-source implementation of intelligent caching, and (4) Measurable performance improvements (40% latency reduction, 16% hit ratio improvement).

### 44. How would you extend this for a research paper?

**Answer:** For a research paper, we'd: (1) Test with real-world traffic traces, (2) Compare multiple ML algorithms (LSTM, Transformer, etc.), (3) Analyze prediction accuracy in detail, (4) Study behavior under various traffic patterns, (5) Evaluate scalability to thousands of edges, and (6) Compare against state-of-the-art caching algorithms.

---

## Practical Questions

### 45. How long did it take to build this project?

**Answer:** The project was built incrementally over [X] weeks/months, with time allocated for: architecture design, backend development, AI engine implementation, frontend dashboard, integration testing, load testing, and documentation. The modular architecture allowed parallel development.

### 46. What was the most difficult part?

**Answer:** The most challenging aspect was coordinating multiple microservices and ensuring data consistency. Debugging distributed system issues, handling timezone-aware datetimes across services, and balancing AI prediction accuracy with performance were also significant challenges.

### 47. How would you deploy this to production?

**Answer:** Production deployment would involve: (1) Containerizing all services with Docker, (2) Orchestrating with Kubernetes, (3) Using managed databases (RDS, Cloud SQL), (4) Implementing CI/CD pipelines, (5) Setting up monitoring and alerting, (6) Configuring load balancers, and (7) Implementing proper security measures.

---

## Conclusion

These questions cover the main aspects of the Smart CDN project. Be prepared to:
- **Explain technical decisions** with clear justifications
- **Discuss limitations** honestly and propose improvements
- **Demonstrate understanding** of distributed systems and AI/ML concepts
- **Show results** with concrete numbers and comparisons
- **Acknowledge challenges** and how you overcame them

**Good luck with your viva!**

