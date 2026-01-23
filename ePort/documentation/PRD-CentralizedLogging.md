# Product Requirements Document: Centralized Logging System

**Version:** 1.0  
**Status:** Draft  
**Date:** January 2026  
**Related:** PRD-MultiProduct.md, ePort-Notifications.md

---

## Executive Summary

Implement a tiered logging system that collects, aggregates, and transmits machine logs to a central store for monitoring, troubleshooting, and analytics across multiple vending machine deployments.

---

## Problem Statement

**Current State:**
- Logs only visible on local Raspberry Pi terminal
- No remote visibility into machine health
- Troubleshooting requires physical access
- No aggregate analytics across machines
- Critical errors not reported in real-time

**Desired State:**
- Remote log viewing and monitoring
- Real-time alerts for critical issues
- Centralized dashboard for all machines
- Historical log analysis and trends
- Proactive issue detection

---

## Goals & Non-Goals

### Goals
1. ✅ Collect logs from multiple vending machines
2. ✅ Send critical events immediately
3. ✅ Batch and compress routine logs
4. ✅ Support both ePort cellular and WiFi delivery
5. ✅ Provide centralized viewing dashboard
6. ✅ Enable log search and filtering

### Non-Goals
- ❌ Video/image logging (too large)
- ❌ Real-time streaming logs (not feasible over cellular)
- ❌ Customer PII in logs (privacy/PCI compliance)
- ❌ Log analysis/ML (future enhancement)

---

## User Stories

### US-1: Operations Team Views Machine Health
**As an** operations manager  
**I want to** view health status of all machines in one dashboard  
**So that** I can identify issues before they cause downtime

**Acceptance Criteria:**
- Dashboard shows all machines with last heartbeat time
- Color-coded status (green/yellow/red) based on recent errors
- Click machine to view recent logs
- Filter by machine, time range, log level

---

### US-2: Technician Troubleshoots Remote Issue
**As a** field technician  
**I want to** view recent error logs before visiting a machine  
**So that** I bring the correct parts and tools

**Acceptance Criteria:**
- Search logs by machine ID
- Filter by ERROR and CRITICAL levels
- View last 24 hours of activity
- Export logs for analysis

---

### US-3: Owner Receives Critical Alerts
**As a** machine owner  
**I want to** receive immediate alerts for critical failures  
**So that** I can respond quickly to revenue-impacting issues

**Acceptance Criteria:**
- SMS/email alert for critical events
- Alert includes: machine ID, issue type, timestamp
- Configurable alert thresholds
- Alert delivery within 5 minutes

---

## Technical Design

### Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                 Vending Machine (Pi)                    │
│                                                         │
│  ┌────────────────────────────────────────────┐       │
│  │  Application Logs                          │       │
│  │  - DEBUG, INFO, WARN, ERROR, CRITICAL      │       │
│  └──────────┬─────────────────────────────────┘       │
│             │                                          │
│             ▼                                          │
│  ┌────────────────────────────────────────────┐       │
│  │  LogRouter                                 │       │
│  │  - Tier 1: Local file (all logs)          │       │
│  │  - Tier 2: ePort buffer (critical/summary) │       │
│  │  - Tier 3: WiFi direct (if available)     │       │
│  └──────┬────────────────────┬────────────────┘       │
│         │                    │                        │
└─────────┼────────────────────┼────────────────────────┘
          │                    │
          │ ePort cellular     │ WiFi (optional)
          ▼                    ▼
┌──────────────────┐  ┌──────────────────┐
│   USAT Server    │  │   Log API        │
│   (USALive)      │  │   (Your Server)  │
└────────┬─────────┘  └────────┬─────────┘
         │                     │
         │ FTP/Email           │ HTTPS
         ▼                     │
┌─────────────────────────────┴──────────────────┐
│         Central Log Store                      │
│  - Log Parser                                  │
│  - Database (PostgreSQL/MongoDB)               │
│  - Search Index (Elasticsearch optional)       │
│  - Alert Engine                                │
└────────────────┬───────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│         Web Dashboard                           │
│  - Machine Status View                         │
│  - Log Search & Filter                         │
│  - Alert Configuration                         │
│  - Analytics & Reports                         │
└─────────────────────────────────────────────────┘
```

---

## New Classes

### 1. LogRouter Class
**Location:** `/Users/travops/soap/ePort/src/log_router.py`

**Responsibilities:**
- Route logs to appropriate destination (local/ePort/WiFi)
- Buffer logs for batch transmission
- Compress logs to meet 900 byte limit
- Handle transmission failures with retry

**Key Methods:**
```python
class LogRouter:
    def __init__(self, eport: EPortProtocol, wifi_enabled: bool):
        self.eport = eport
        self.wifi_enabled = wifi_enabled
        self.local_file = open('/var/log/vending_machine.log', 'a')
        self.eport_buffer = LogBuffer(max_size=800)
        self.last_send_time = time.time()
    
    def route_log(self, level: str, message: str, context: Dict) -> None:
        """Route log to appropriate destinations"""
        
    def send_critical_immediate(self, log_entry: Dict) -> bool:
        """Send critical log immediately via best available method"""
        
    def send_batch(self) -> bool:
        """Send batched logs periodically"""
        
    def compress_logs(self, logs: List[Dict]) -> str:
        """Compress logs to fit 900 byte limit"""
```

---

### 2. LogBuffer Class
**Location:** `/Users/travops/soap/ePort/src/log_buffer.py`

**Responsibilities:**
- Maintain circular buffer of recent logs
- Enforce size limits
- Provide formatted output for transmission

**Key Methods:**
```python
class LogBuffer:
    def __init__(self, max_size: int = 800):
        self.events = []
        self.max_size = max_size
    
    def add_event(self, timestamp: str, level: str, message: str) -> None:
        """Add event, maintaining size limit"""
        
    def get_log_data(self) -> str:
        """Get formatted log data for transmission"""
        
    def get_size(self) -> int:
        """Calculate current buffer size in bytes"""
        
    def clear(self) -> None:
        """Clear buffer after successful transmission"""
```

---

### 3. LogCompressor Class
**Location:** `/Users/travops/soap/ePort/src/log_compressor.py`

**Responsibilities:**
- Compress logs to fit 900 byte limit
- Aggregate similar events
- Truncate less important data
- Maintain critical information

**Key Methods:**
```python
class LogCompressor:
    @staticmethod
    def compress_logs(logs: List[Dict], max_bytes: int = 900) -> str:
        """Compress logs to fit byte limit"""
        
    @staticmethod
    def aggregate_events(logs: List[Dict]) -> List[Dict]:
        """Aggregate similar events (e.g., 5x 'Card declined')"""
        
    @staticmethod
    def truncate_messages(logs: List[Dict], max_msg_len: int = 50) -> List[Dict]:
        """Truncate log messages to fit size constraints"""
```

---

### 4. CentralLogClient Class
**Location:** `/Users/travops/soap/ePort/src/central_log_client.py`

**Responsibilities:**
- Send logs to central API (if WiFi available)
- Handle authentication
- Retry failed transmissions
- Queue logs during network outages

**Key Methods:**
```python
class CentralLogClient:
    def __init__(self, api_url: str, machine_id: str, api_key: str):
        self.api_url = api_url
        self.machine_id = machine_id
        self.api_key = api_key
        self.queue = []
    
    def send_logs(self, logs: List[Dict]) -> bool:
        """Send logs to central API"""
        
    def send_critical_alert(self, log_entry: Dict) -> bool:
        """Send critical alert with high priority"""
        
    def queue_for_retry(self, logs: List[Dict]) -> None:
        """Queue logs for retry if transmission fails"""
```

---

## Log Format

### Standard Log Entry

```python
{
    "timestamp": "2026-01-22T14:30:15.123Z",
    "machine_id": "VM001",
    "level": "ERROR",
    "component": "payment",
    "message": "Authorization timeout after 30s",
    "context": {
        "transaction_id": "abc123",
        "amount_cents": 2000,
        "retry_count": 3
    }
}
```

### Compressed Format (for ePort transmission)

```
VM001|0122-1430|E|payment|Auth timeout 30s|txn:abc123
VM001|0122-1435|W|motor|GPIO conflict retry 2
VM001|0122-1440|I|txn|47 completed $142.35
```

**Format:** `MACHINE|MMDD-HHMM|L|COMPONENT|MESSAGE|CONTEXT`

**Legend:**
- `MACHINE` - Machine ID (5 chars)
- `MMDD-HHMM` - Compact timestamp (9 chars)
- `L` - Level (E/W/I/C = Error/Warn/Info/Critical)
- `COMPONENT` - Component name (truncated)
- `MESSAGE` - Truncated message (max 30 chars)
- `CONTEXT` - Key context data (optional, truncated)

---

## Transmission Strategies

### Tier 1: Local File (Always)

**Purpose:** Full detailed logs for local troubleshooting

**Configuration:**
```python
# Standard Python logging
logging.basicConfig(
    filename='/var/log/vending_machine.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5  # Keep 5 rotated files
)
```

**Retention:** 50MB total (10MB × 5 files)

---

### Tier 2: ePort Cellular (Critical + Summaries)

**Purpose:** Send critical events and hourly summaries without WiFi

**Transmission Schedule:**
- **Immediate:** CRITICAL level events
- **Hourly:** Compressed batch of ERROR/WARN events
- **Daily:** Summary statistics

**Compression Strategy:**
```python
def compress_for_eport(logs: List[Dict]) -> str:
    """Compress logs to <900 bytes"""
    compressed = []
    
    # Group by component and count duplicates
    grouped = {}
    for log in logs:
        key = f"{log['component']}:{log['message'][:20]}"
        grouped[key] = grouped.get(key, 0) + 1
    
    # Format: COMPONENT|MESSAGE|COUNT
    for key, count in grouped.items():
        component, msg = key.split(':', 1)
        if count > 1:
            compressed.append(f"{component}|{msg}|x{count}")
        else:
            compressed.append(f"{component}|{msg}")
    
    # Join and truncate to 900 bytes
    result = "\n".join(compressed)
    return result[:900]
```

---

### Tier 3: WiFi Direct (Full Logs, If Available)

**Purpose:** Send complete logs when WiFi is available

**Transmission Schedule:**
- **Immediate:** CRITICAL and ERROR events
- **Every 5 minutes:** Batched WARN and INFO events
- **Continuous:** Full log streaming (if bandwidth allows)

**API Format:**
```python
# POST to central API
{
    "machine_id": "VM001",
    "logs": [
        {
            "timestamp": "2026-01-22T14:30:15.123Z",
            "level": "ERROR",
            "component": "payment",
            "message": "Authorization timeout",
            "context": {...}
        },
        ...
    ]
}
```

---

## Central Log Store

### Database Schema

**Table: machines**
```sql
CREATE TABLE machines (
    id VARCHAR(10) PRIMARY KEY,
    name VARCHAR(100),
    location VARCHAR(200),
    last_heartbeat TIMESTAMP,
    status VARCHAR(20), -- online, offline, error
    created_at TIMESTAMP
);
```

**Table: logs**
```sql
CREATE TABLE logs (
    id SERIAL PRIMARY KEY,
    machine_id VARCHAR(10) REFERENCES machines(id),
    timestamp TIMESTAMP,
    level VARCHAR(10),
    component VARCHAR(50),
    message TEXT,
    context JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_logs_machine_time ON logs(machine_id, timestamp DESC);
CREATE INDEX idx_logs_level ON logs(level);
```

**Table: alerts**
```sql
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    machine_id VARCHAR(10) REFERENCES machines(id),
    log_id INTEGER REFERENCES logs(id),
    alert_type VARCHAR(50),
    severity VARCHAR(20),
    status VARCHAR(20), -- pending, sent, acknowledged
    sent_at TIMESTAMP,
    acknowledged_at TIMESTAMP
);
```

---

### Log API Endpoints

**POST /api/logs**
- Accept batch of logs from machine
- Authenticate via API key
- Store in database
- Trigger alerts if needed

**GET /api/logs**
- Query logs with filters (machine, time range, level)
- Pagination support
- Return JSON array of logs

**GET /api/machines/{id}/status**
- Get current machine status
- Last heartbeat, error count, uptime

**POST /api/alerts/configure**
- Configure alert rules
- Set thresholds and notification channels

---

## Dashboard Features

### 1. Machine Status Overview

```
┌─────────────────────────────────────────────────┐
│  VENDING MACHINE FLEET STATUS                   │
├─────────────────────────────────────────────────┤
│  🟢 VM001  Last: 2 min ago   Errors: 0         │
│  🟢 VM002  Last: 1 min ago   Errors: 0         │
│  🟡 VM003  Last: 15 min ago  Errors: 2         │
│  🔴 VM004  Last: 2 hrs ago   Errors: 12  ⚠️    │
│  🟢 VM005  Last: 30 sec ago  Errors: 0         │
└─────────────────────────────────────────────────┘
```

---

### 2. Log Viewer

```
┌─────────────────────────────────────────────────┐
│  LOG VIEWER - VM003                             │
├─────────────────────────────────────────────────┤
│  Filters: [ERROR ▼] [Last 24h ▼] [All Components ▼]
│                                                  │
│  2026-01-22 14:30:15 ERROR payment              │
│  Authorization timeout after 30s                │
│  Context: txn_id=abc123, amount=$20.00          │
│                                                  │
│  2026-01-22 14:32:20 ERROR motor                │
│  GPIO conflict on pin 17, retry 2               │
│  Context: product=soap_hand                     │
│                                                  │
│  2026-01-22 14:35:10 WARN flowmeter             │
│  Pulse count mismatch, recalibrating            │
│  Context: expected=54, actual=52                │
└─────────────────────────────────────────────────┘
```

---

### 3. Alert Configuration

```
┌─────────────────────────────────────────────────┐
│  ALERT RULES                                    │
├─────────────────────────────────────────────────┤
│  Rule 1: Critical Hardware Failure              │
│  Trigger: Any CRITICAL level log               │
│  Action: SMS + Email immediately                │
│  Recipients: ops@example.com, +1234567890       │
│                                                  │
│  Rule 2: Multiple Payment Failures              │
│  Trigger: 5+ payment errors in 10 minutes       │
│  Action: Email within 5 minutes                 │
│  Recipients: support@example.com                │
│                                                  │
│  Rule 3: Machine Offline                        │
│  Trigger: No heartbeat for 30 minutes           │
│  Action: SMS immediately                        │
│  Recipients: ops@example.com                    │
└─────────────────────────────────────────────────┘
```

---

## Configuration

### Add to config/__init__.py

```python
# Centralized logging configuration
LOG_ROUTER_ENABLED = True
LOG_MACHINE_ID = "VM001"  # Unique machine identifier

# Local file logging
LOG_LOCAL_PATH = "/var/log/vending_machine.log"
LOG_LOCAL_LEVEL = "DEBUG"  # Log everything locally
LOG_LOCAL_MAX_BYTES = 10 * 1024 * 1024  # 10MB
LOG_LOCAL_BACKUP_COUNT = 5

# ePort cellular logging
LOG_EPORT_ENABLED = True
LOG_EPORT_BUFFER_SIZE = 800  # Bytes (leave room for headers)
LOG_EPORT_SEND_INTERVAL = 3600  # Send batch every hour
LOG_EPORT_CRITICAL_IMMEDIATE = True  # Send CRITICAL immediately
LOG_EPORT_LEVELS = ["CRITICAL", "ERROR", "WARN"]  # Don't send INFO/DEBUG

# WiFi logging (if available)
LOG_WIFI_ENABLED = False  # Set to True if WiFi available
LOG_WIFI_API_URL = "https://logs.yourserver.com/api/logs"
LOG_WIFI_API_KEY = "your-api-key-here"
LOG_WIFI_SEND_INTERVAL = 300  # Send batch every 5 minutes
LOG_WIFI_RETRY_ATTEMPTS = 3
LOG_WIFI_RETRY_DELAY = 60

# Log compression
LOG_COMPRESS_ENABLED = True
LOG_MESSAGE_MAX_LENGTH = 50  # Truncate messages for compression
LOG_AGGREGATE_DUPLICATES = True  # Group similar events

# Heartbeat
LOG_HEARTBEAT_INTERVAL = 300  # Send heartbeat every 5 minutes
LOG_HEARTBEAT_INCLUDE_STATS = True  # Include basic stats in heartbeat
```

---

## Implementation Phases

### Phase 1: Local Logging Enhancement (Week 1)
- [ ] Implement LogRouter class
- [ ] Add structured logging format
- [ ] Test local file rotation
- [ ] Add machine ID to all logs

### Phase 2: ePort Transmission (Week 2)
- [ ] Implement LogBuffer class
- [ ] Implement LogCompressor class
- [ ] Add ePort file transfer commands
- [ ] Test 900 byte limit handling
- [ ] Implement critical event immediate send

### Phase 3: Central Log Store (Week 3)
- [ ] Set up database schema
- [ ] Implement log API endpoints
- [ ] Set up USAT FTP/email forwarding
- [ ] Test log parsing and storage

### Phase 4: Dashboard & Alerts (Week 4)
- [ ] Build web dashboard
- [ ] Implement log search and filtering
- [ ] Configure alert rules
- [ ] Set up SMS/email notifications
- [ ] Test end-to-end flow

### Phase 5: WiFi Support (Optional)
- [ ] Implement CentralLogClient class
- [ ] Add WiFi detection and fallback
- [ ] Test hybrid approach (WiFi + ePort)
- [ ] Optimize batch sizes

---

## Log Compression Examples

### Before Compression (450 bytes)
```json
[
  {"timestamp": "2026-01-22T14:30:15Z", "level": "ERROR", "component": "payment", "message": "Authorization timeout after 30 seconds", "context": {"txn": "abc123"}},
  {"timestamp": "2026-01-22T14:32:20Z", "level": "ERROR", "component": "motor", "message": "GPIO conflict on pin 17, retry attempt 2", "context": {"product": "soap_hand"}},
  {"timestamp": "2026-01-22T14:35:10Z", "level": "WARN", "component": "flowmeter", "message": "Pulse count mismatch, recalibrating sensor", "context": {"expected": 54, "actual": 52}}
]
```

### After Compression (187 bytes)
```
VM001|0122-1430|E|pay|Auth timeout 30s|abc123
VM001|0122-1432|E|mtr|GPIO17 retry2|soap_hand
VM001|0122-1435|W|flw|Pulse mismatch recal|54>52
```

**Compression Ratio:** 58% reduction

---

## Alert Rules

### Critical Alerts (Immediate)

| Event | Trigger | Action | Channels |
|-------|---------|--------|----------|
| Hardware Failure | CRITICAL level log | Immediate | SMS + Email |
| Payment System Down | 10+ payment errors in 5 min | Within 1 min | SMS + Email |
| Machine Offline | No heartbeat 30+ min | Within 5 min | SMS |
| Security Breach | Tamper detection | Immediate | SMS + Email + Call |

### Warning Alerts (Batched)

| Event | Trigger | Action | Channels |
|-------|---------|--------|----------|
| Low Inventory | Product < threshold | Daily digest | Email |
| Elevated Errors | 5+ errors in hour | Hourly digest | Email |
| Connectivity Issues | Intermittent network | Daily digest | Email |

---

## Security & Privacy

### Data Protection

1. **No Customer PII**
   - Don't log card numbers
   - Don't log customer names
   - Hash transaction IDs

2. **API Authentication**
   - Use API keys for log submission
   - Rotate keys quarterly
   - HTTPS only for transmission

3. **Access Control**
   - Role-based dashboard access
   - Audit log viewing activity
   - Encrypt logs at rest

---

## Testing Strategy

### Unit Tests
- LogRouter routing logic
- LogBuffer size management
- LogCompressor compression accuracy
- CentralLogClient retry logic

### Integration Tests
- End-to-end log flow (Pi → ePort → Server)
- WiFi fallback to ePort
- Alert triggering and delivery
- Dashboard log queries

### Load Tests
- Handle 1000 logs/hour per machine
- Support 100 machines simultaneously
- Dashboard performance with 1M+ logs

---

## Success Metrics

### Functional
- ✅ 95%+ log delivery success rate
- ✅ Critical alerts delivered < 5 minutes
- ✅ Dashboard load time < 2 seconds
- ✅ Zero log data loss

### Operational
- 📊 MTTR (Mean Time To Resolution) reduced 50%
- 📊 Remote troubleshooting success rate > 80%
- 📊 Proactive issue detection > 70%

---

## Future Enhancements

### Phase 2 Features
- [ ] Log analytics and trends
- [ ] Predictive maintenance alerts
- [ ] Machine learning anomaly detection
- [ ] Mobile app for alerts
- [ ] Integration with ticketing system
- [ ] Automated diagnostics

---

## Cost Considerations

### ePort Cellular Data
- Estimate: 1-2 MB/month per machine
- Check USAT plan data allowance
- Monitor for overages

### Central Server
- Small deployment: Heroku/DigitalOcean (~$20/month)
- Medium: AWS/GCP (~$50-100/month)
- Large: Dedicated infrastructure

### SMS Alerts
- ~$0.01 per SMS
- Budget for critical alerts only

---

## Open Questions

### Q1: Log Retention Period
**Question:** How long to keep logs in central store?  
**Options:**
- 30 days: Minimal storage cost
- 90 days: Quarterly analysis
- 1 year: Annual trends

**Recommendation:** 90 days active, archive to S3 for 1 year

---

### Q2: Real-Time vs Batch
**Question:** Balance between real-time delivery and data costs  
**Recommendation:** Critical immediate, others batched hourly

---

### Q3: Log Level Defaults
**Question:** What level to send via ePort vs WiFi?  
**Recommendation:** 
- ePort: CRITICAL, ERROR, WARN
- WiFi: All levels (DEBUG, INFO, WARN, ERROR, CRITICAL)

---

## Dependencies

### Python Packages
```txt
# Add to requirements.txt
requests>=2.28.0  # For WiFi log transmission
python-json-logger>=2.0.0  # Structured logging
```

### Infrastructure
- PostgreSQL or MongoDB (log storage)
- Web server (Flask/FastAPI for API)
- Frontend (React/Vue for dashboard)
- SMTP server (email alerts)
- SMS service (Twilio or SNS)

---

## Summary

**Key Takeaways:**

1. **Tiered Approach:** Local file + ePort cellular + WiFi (optional)
2. **Compression Required:** 900 byte limit needs smart compression
3. **Critical First:** Prioritize immediate delivery of critical events
4. **Batch Routine:** Aggregate and send non-critical logs hourly
5. **Centralized Monitoring:** Single dashboard for all machines
6. **Proactive Alerts:** Detect issues before they cause downtime

This logging system provides visibility into machine health without requiring WiFi at every location, using ePort's cellular connection as a reliable backup.

---

**Document Status:** Ready for Review  
**Implementation Complexity:** High (4-5 weeks)  
**Dependencies:** ePort-Notifications.md, PRD-MultiProduct.md  
**Next Steps:** Review → Approve → Phase 1 Implementation
