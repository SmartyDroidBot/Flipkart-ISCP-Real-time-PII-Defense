
# Deployment Strategy for PII Detector & Redactor (Hybrid Regex + NER)


## Recommended Architecture: API Gateway Plugin (Sidecar/Filter) with Hybrid Detection

### Where to Deploy
- **API Gateway Layer** (e.g., Kong, NGINX, Envoy, AWS API Gateway) as a plugin/filter/sidecar.
- Optionally, as a DaemonSet in Kubernetes for all ingress/egress traffic.

### Why This Layer?
- **Scalability:** API Gateways are horizontally scalable and already handle all ingress/egress traffic.
- **Latency:** Minimal, as the plugin can be written in a compiled language (Go, Rust) or as a fast Python microservice. Redaction is regex/NER-based and fast. For NER/ML, ensure sufficient CPU (or GPU for high throughput) is available.
- **Cost-Effectiveness:** No need to modify application code. Centralized enforcement reduces dev/ops overhead.
- **Integration:** Easy to add as a filter/plugin. Can be enabled/disabled per route/service. Works for REST, GraphQL, gRPC, etc.
- **Security:** Ensures all data leaving/entering the org is sanitized, regardless of app team diligence.


### How It Works (Hybrid)
- The plugin intercepts all API requests/responses.
- For each payload (JSON, CSV, etc.), it runs the PII detector/redactor using:
	- **Regex** for well-structured fields (phone, aadhar, etc.)
	- **NER/ML (spaCy)** for unstructured/free-text fields (descriptions, queries, etc.)
- If PII is found, it redacts/masks before forwarding to the next hop.
- Logs all redaction events for audit.
- Can be extended to block, alert, or quarantine suspicious payloads.
- If NER/ML model is unavailable, fallback to regex-only mode (resilient by design).


### Deployment Steps
1. **Containerize** the Python detector/redactor (with spaCy model) as a microservice or plugin.
2. **Integrate** with API Gateway (as a plugin, filter, or sidecar container).
3. **Configure** routes/services to use the plugin for relevant endpoints.
4. **Monitor** logs and metrics for redaction events, performance, and model health.
5. **Model Management:** Ensure spaCy/ML models are versioned and updated as needed. Use CI/CD for plugin and model updates.
6. **Fallback Logic:** If NER/ML is unavailable, automatically use regex-only mode.
7. **Iterate:** Tune regex/NER rules as new PII patterns emerge. Monitor for model drift or new PII types.

### Alternatives Considered
- **App Layer SDK:** High dev effort, inconsistent coverage.
- **Browser Extension:** Only protects UI, not backend leaks.
- **Database Layer:** Too late; PII may already be leaked.
- **BotManager Plugin:** Good for scraping, but not for all PII flows.

### Diagram
```
[Client] <--> [API Gateway + PII Plugin] <--> [App Servers] <--> [DB]
```


### Summary
- **Hybrid approach** (regex + NER/ML) maximizes detection accuracy for both structured and unstructured data.
- **Best tradeoff** between coverage, latency, and cost.
- **Centralized, scalable, and easy to maintain.**
- **No app code changes required.**
- **Resilient:** Fallback to regex-only mode if NER/ML is unavailable.
