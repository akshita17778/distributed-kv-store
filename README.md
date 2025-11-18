# Distributed Key-Value Store

A fully working distributed key-value store implementation with consistent hashing, replication, and TCP socket communication. No external APIs or cloud dependencies — everything runs locally.

## Table of Contents

- [Architecture](#architecture)
- [Features](#features)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Usage Examples](#usage-examples)
- [Consistent Hashing](#consistent-hashing)
- [Replication](#replication)
- [Design Advantages](#design-advantages)

---

## Architecture

The system consists of three main components:

### 1. **Coordinator Server**
- Central node registry and metadata service
- Maintains a consistent hash ring of all active nodes
- Handles node registration and failure detection
- Returns primary + replica nodes for any given key

### 2. **Node Servers**
- Store key-value pairs in memory
- Register themselves with the coordinator on startup
- Accept PUT/GET/DELETE operations from clients
- Replicate data to assigned replica nodes
- Communicate directly with clients (not through coordinator)

### 3. **Client**
- Queries coordinator for node locations
- Connects directly to primary node for operations
- Falls back to replicas on primary failure
- Provides interactive CLI or single-command mode

### System Diagram

```
┌─────────────────────────────────────────────────────────┐
│                      Client                             │
│  (Queries Coordinator, Communicates with Nodes)        │
└────────────────┬────────────────────────────────────────┘
                 │ Query: "Which node has key X?"
                 ▼
        ┌────────────────────┐
        │   Coordinator      │
        │   (Port 5000)      │
        │                    │
        │ • Node Registry    │
        │ • Hash Ring        │
        │ • Failure Detect   │
        └───┬────────────────┘
            │ Response: Primary + Replicas
            │
    ┌───────┴────────────────────────────┐
    │                                    │
    ▼ PUT/GET/DELETE                    ▼ Replication
    │                                    │
┌───────────┐    Primary            ┌──────────┐
│ Node 1    │ ────────────────────▶ │ Node 2   │
│ (Port     │ Replicates data      │ (Port    │
│  5001)    │◀─────────────────────│  5002)   │
└───────────┘  Replica             └──────────┘
    │                                   │
    └───────────────────────┬───────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │ Node 3       │
                    │ (Port 5003)  │
                    │ Replica      │
                    └──────────────┘
```

---

## Features

✅ **Consistent Hashing**
- SHA-256 based hash function
- Virtual nodes for better key distribution
- Minimal key redistribution on node failures

✅ **Replication**
- 1 Primary + 2 Replicas for each key
- Primary pushes data to replicas synchronously
- Read fallback to replicas if primary fails

✅ **Node Management**
- Automatic node registration with coordinator
- Heartbeat-based failure detection
- Dead nodes removed from the hash ring

✅ **Pure TCP Communication**
- No external libraries or cloud APIs
- Text-based protocol (easy to debug)
- Direct node-to-node replication

✅ **Thread-Safe Operations**
- Mutex locks on shared data
- Concurrent client handling

---

## Project Structure

```
distributed-kv-store/
├── coordinator/
│   └── coordinator.py       # Coordinator server
├── node/
│   └── node.py              # Node server (multi-instance)
├── client/
│   └── client.py            # Client CLI
├── hashing.py               # Consistent hashing ring
└── README.md                # This file
```

---

## Getting Started

### Prerequisites
- Python 3.7+
- No external dependencies (uses only stdlib)

### 1. Start the Coordinator

```bash
python coordinator/coordinator.py
```

Expected output:
```
[Coordinator] Started on 127.0.0.1:5000
```

The coordinator listens on `127.0.0.1:5000` by default.

### 2. Start Node Servers

Open new terminal windows and start multiple nodes:

```bash
# Terminal 1: Node 1
python node/node.py 5001

# Terminal 2: Node 2
python node/node.py 5002

# Terminal 3: Node 3
python node/node.py 5003
```

Expected output for each node:
```
[Node 5001] Coordinator response: OK Node 127.0.0.1:5001 registered
[Node 5001] Started on 127.0.0.1:5001
```

### 3. Run the Client

```bash
# Interactive mode
python client/client.py

# Or single command mode
python client/client.py --command "PUT user:1 Alice"
python client/client.py --command "GET user:1"
```

---

## Usage Examples

### Interactive Mode

```bash
$ python client/client.py

=== Distributed KV Store Client ===
Commands:
  PUT key value     - Store a key-value pair
  GET key           - Retrieve a value
  DELETE key        - Delete a key-value pair
  LIST_NODES        - List all registered nodes
  EXIT              - Exit the shell

>> PUT user:1 Alice
[Client] PUT user:1 = Alice [primary: 127.0.0.1:5001, replicas: ['127.0.0.1:5002', '127.0.0.1:5003']]

>> GET user:1
[Client] GET user:1 = Alice

>> DELETE user:1
[Client] DELETE user:1 [primary: 127.0.0.1:5001]

>> LIST_NODES
OK Nodes:
  127.0.0.1:5001
  127.0.0.1:5002
  127.0.0.1:5003

>> EXIT
Goodbye!
```

### Single Command Mode

```bash
# Store a value
$ python client/client.py --command "PUT cache:session:123 {\"user_id\": 456, \"ttl\": 3600}"
[Client] PUT cache:session:123 = {"user_id": 456, "ttl": 3600} [primary: 127.0.0.1:5002, replicas: ...]

# Retrieve a value
$ python client/client.py --command "GET cache:session:123"
[Client] GET cache:session:123 = {"user_id": 456, "ttl": 3600}

# Delete a value
$ python client/client.py --command "DELETE cache:session:123"
[Client] DELETE cache:session:123 [primary: 127.0.0.1:5002]
```

### Testing Failure Recovery

1. **Stop a node** (Ctrl+C on that node's terminal)
2. **Verify data is on replicas**

   ```bash
   >> GET user:1
   [Client] Primary node failed, trying replicas...
   [Client] GET user:1 = Alice (from replica 127.0.0.1:5003)
   ```

3. **Coordinator removes dead node**

   ```
   [Coordinator] Node 127.0.0.1:5001 marked as dead and removed
   ```

---

## Consistent Hashing

### How It Works

1. **Hash Ring**: Keys and nodes are mapped to a 256-bit circular hash space using SHA-256
2. **Virtual Nodes**: Each physical node gets 3 virtual nodes for better distribution
3. **Key Lookup**: For any key, find the first node clockwise on the ring

### Example

```
Hash Ring (simplified):
0 ─────── Node1:virt1 ─────── Node2:virt1 ─────── Node3:virt1 ─────── 2^256

For key "user:100":
  hash("user:100") → position on ring
  ↓
  First node clockwise: Node2
  ↓
  Node2 is PRIMARY, next 2 clockwise = REPLICAS
```

### Benefits

- **Minimal Redistribution**: Adding/removing a node only affects ~1/N keys
- **Fault Tolerance**: If a node fails, its keys move to the next nodes
- **Scalability**: New nodes seamlessly join the cluster

---

## Replication

### How It Works

1. **Client Requests PUT** → Coordinator returns primary + 2 replicas
2. **Primary Node Stores** the key-value pair locally
3. **Primary Sends REPLICATE** commands to both replicas (asynchronous)
4. **Replicas Store** the data without responding
5. **Primary Confirms OK** to client

### Failure Scenarios

| Scenario | Outcome |
|----------|---------|
| Primary fails after PUT | Data is safe on 2 replicas |
| Client issues GET on dead primary | Client falls back to replica |
| 1 Replica fails | 2 copies still exist (1 primary + 1 replica) |
| 2 Replicas fail | Data still on primary |
| Primary + 1 Replica fail | 1 replica still has data, client can read it |

---

## Design Advantages

### ✅ Pros

1. **No Single Point of Failure**: Data is replicated 3 ways
2. **Horizontal Scalability**: Add nodes without downtime
3. **Low Latency**: No network hops after coordinator lookup
4. **Simple Protocol**: Text-based, easy to debug and extend
5. **Thread-Safe**: Concurrent operations supported
6. **Fair Distribution**: Virtual nodes ensure balanced load

### ⚠️ Limitations

1. **In-Memory Only**: Data lost if all replicas crash
2. **Eventual Consistency**: Replicas may lag if primary fails mid-replication
3. **No Persistence**: No disk I/O (could be added)
4. **No Transactions**: No multi-key atomic operations
5. **Simple Failure Detection**: Only heartbeat-based (no gossip protocol)

### 🔧 Potential Improvements

- **Persistence**: Write to disk (RocksDB, SQLite, etc.)
- **Gossip Protocol**: Peer-to-peer failure detection
- **Conflict Resolution**: Last-write-wins, vector clocks, etc.
- **Load Balancing**: Read requests to any replica
- **Compression**: Compress large values
- **Expiration**: TTL-based key expiration
- **Snapshots**: Periodic data snapshots for recovery

---

## API Reference

### Coordinator Commands

| Command | Format | Response |
|---------|--------|----------|
| Register Node | `REGISTER_NODE host port` | `OK Node host:port registered` |
| Unregister Node | `UNREGISTER_NODE host port` | `OK Node host:port unregistered` |
| Get Nodes for Key | `GET_NODES_FOR_KEY key` | `PRIMARY host:port\nREPLICA host:port\nREPLICA host:port` |
| List Nodes | `LIST_NODES` | `OK Nodes:\n  host1:port1\n  host2:port2\n  ...` |

### Node Commands

| Command | Format | Response |
|---------|--------|----------|
| Put | `PUT key value [replicas]` | `OK` |
| Get | `GET key` | `VALUE value` or `NOT_FOUND` |
| Delete | `DELETE key` | `OK` |
| Replicate | `REPLICATE key value` | `OK` |
| Info | `INFO` | `OK Node host:port keys=N` |

### Client Commands

| Command | Usage |
|---------|-------|
| Put | `PUT key value` |
| Get | `GET key` |
| Delete | `DELETE key` |
| List Nodes | `LIST_NODES` |
| Exit | `EXIT` |

---

## Troubleshooting

### "Connection refused" from client
- **Cause**: Coordinator or nodes not running
- **Fix**: Ensure coordinator is running on port 5000, nodes on 5001+

### "Node not found" error
- **Cause**: No nodes registered yet
- **Fix**: Start at least one node before querying

### Data loss after node crash
- **Cause**: Only one replica was running
- **Fix**: Always run at least 3 nodes for full replication coverage

### Slow replication
- **Cause**: Network latency or node overload
- **Fix**: Async replication is normal; monitor node CPU/network

---

## License

MIT License. Use freely for learning and development.

---

## Author

Created as a demonstration of distributed systems concepts: consistent hashing, replication, and fault tolerance.
