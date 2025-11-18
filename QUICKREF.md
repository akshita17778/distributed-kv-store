# QUICK REFERENCE GUIDE

## File Overview

| File | Purpose | Language |
|------|---------|----------|
| `coordinator/coordinator.py` | Central coordinator server | Python |
| `node/node.py` | Node server (run 3+ instances) | Python |
| `client/client.py` | Client CLI and API | Python |
| `hashing.py` | Consistent hash ring implementation | Python |
| `test.py` | Automated test suite | Python |
| `README.md` | Full documentation | Markdown |
| `quickstart.bat` | Windows quick start guide | Batch |
| `quickstart.sh` | Linux/Mac quick start guide | Bash |

## Quick Commands

### Windows PowerShell

```powershell
# Terminal 1: Coordinator
python coordinator/coordinator.py

# Terminal 2: Node 1
python node/node.py 5001

# Terminal 3: Node 2
python node/node.py 5002

# Terminal 4: Node 3
python node/node.py 5003

# Terminal 5: Client (interactive)
python client/client.py

# Or single command:
python client/client.py --command "PUT key value"
```

### Linux / Mac

```bash
# Terminal 1: Coordinator
python3 coordinator/coordinator.py

# Terminal 2-4: Nodes
python3 node/node.py 5001
python3 node/node.py 5002
python3 node/node.py 5003

# Terminal 5: Client
python3 client/client.py
```

## Client Commands (Interactive Mode)

```
PUT key value      # Store a key-value pair
GET key            # Retrieve a value
DELETE key         # Delete a key-value pair
LIST_NODES         # Show all registered nodes
EXIT               # Quit client
```

## Example Session

```
$ python client/client.py

=== Distributed KV Store Client ===
...

>> PUT user:alice {"age": 30, "email": "alice@example.com"}
[Client] PUT user:alice = {"age": 30, "email": "alice@example.com"} [primary: 127.0.0.1:5001, replicas: ['127.0.0.1:5002', '127.0.0.1:5003']]

>> GET user:alice
[Client] GET user:alice = {"age": 30, "email": "alice@example.com"}

>> DELETE user:alice
[Client] DELETE user:alice [primary: 127.0.0.1:5001]

>> LIST_NODES
OK Nodes:
  127.0.0.1:5001
  127.0.0.1:5002
  127.0.0.1:5003

>> EXIT
Goodbye!
```

## Testing Replication & Failover

### 1. Start full system (3 nodes)
```
Coordinator on 5000 ✓
Node1 on 5001 ✓
Node2 on 5002 ✓
Node3 on 5003 ✓
```

### 2. Store data
```
>> PUT mydata "important value"
[primary: 127.0.0.1:5001, replicas: ['127.0.0.1:5002', '127.0.0.1:5003']]
```

### 3. Verify data
```
>> GET mydata
"important value" ✓
```

### 4. Kill primary node (Ctrl+C on Node1)
```
[Coordinator] Node 127.0.0.1:5001 marked as dead and removed
```

### 5. Retrieve from replicas
```
>> GET mydata
[Client] Primary node failed, trying replicas...
[Client] GET mydata = "important value" (from replica 127.0.0.1:5002) ✓
```

## Key Features Demonstrated

✅ **Distributed Architecture**: Coordinator + Multiple Nodes + Client
✅ **Consistent Hashing**: Keys distributed across nodes using SHA-256
✅ **Replication**: 1 Primary + 2 Replicas for high availability
✅ **Failure Detection**: Heartbeat-based node health monitoring
✅ **Failover**: Automatic fallback to replicas
✅ **TCP Communication**: Direct node-to-node, no external services
✅ **Thread-Safe**: Concurrent operations with mutex locks

## Architecture Summary

```
CLIENT (python client/client.py)
   ↓
   ├─→ Query Coordinator (5000): "Which node has key X?"
   │
   └─→ Connect to Primary Node (5001/5002/5003)
       ├─→ PUT/GET/DELETE operation
       │
       └─→ Primary replicates to 2 Replicas
           ├─→ Replica A (5002)
           └─→ Replica B (5003)
```

## Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| "Connection refused" | Services not running | Start coordinator, then nodes |
| "No nodes available" | Ring is empty | Start at least 1 node |
| "NOT_FOUND" | Key not stored | Store key first with PUT |
| Slow responses | Node overload | Distribute load across nodes |
| Data loss | Single node crash | Run 3+ nodes for redundancy |

## Performance Notes

- **Latency**: O(1) key lookup via hash ring + O(1) in-memory storage
- **Replication**: Synchronous (waits for all replicas before confirming)
- **Scalability**: Horizontal (add more nodes linearly increases capacity)
- **Consistency**: Strong (all replicas get identical copies)

## Next Steps to Enhance

1. **Persistence**: Add RocksDB or SQLite for disk storage
2. **Gossip Protocol**: Peer-to-peer failure detection
3. **TTL**: Automatic key expiration
4. **Snapshots**: Periodic data backups
5. **Compression**: Compress large values
6. **Async Replication**: Non-blocking replica updates
7. **Read Replicas**: Distribute read load to any replica
8. **REST API**: HTTP interface instead of just TCP

## License

MIT - Free to use, modify, and distribute for educational purposes.
