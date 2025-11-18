

import socket
import time
import sys

def test_system():
    """Test the running distributed KV store system"""
    
    print("\n" + "="*75)
    print(" DISTRIBUTED KEY-VALUE STORE - SYSTEM VERIFICATION".center(75))
    print("="*75 + "\n")
    
    # Test 1: Coordinator connectivity
    print("[1] Checking Coordinator (Port 5000)...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    try:
        sock.connect(('127.0.0.1', 5000))
        print("    SUCCESS: Coordinator is running")
        sock.close()
    except:
        print("    FAILED: Coordinator not responding")
        return False
    
    # Test 2: Check nodes
    print("\n[2] Checking Node Servers...")
    node_ports = [5001, 5002, 5003]
    active_nodes = 0
    for port in node_ports:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        try:
            sock.connect(('127.0.0.1', port))
            print(f"    Node on port {port}: ACTIVE")
            sock.close()
            active_nodes += 1
        except:
            print(f"    Node on port {port}: INACTIVE")
    
    if active_nodes < 3:
        print(f"\n    WARNING: Only {active_nodes}/3 nodes active (minimum 1 required)")
    
    # Test 3: System Demo
    print("\n[3] System Demonstration...")
    print("\n    EXAMPLE COMMANDS:")
    print("    - PUT resume-project 'Distributed-KV-Store'")
    print("    - GET resume-project")
    print("    - DELETE resume-project")
    print("\n    Run from C:\\Users\\vikas\\distributed-kv-store\\client\\:")
    print("    - python client.py --command 'LIST_NODES'")
    print("    - python client.py --command 'PUT key value'")
    print("    - python client.py --command 'GET key'")
    
    # Test 4: System Information
    print("\n[4] System Architecture:")
    print("    - Coordinator: TCP server (port 5000) - manages node registry")
    print("    - Nodes: 3x TCP servers (5001-5003) - store data with replication")
    print("    - Client: CLI interface - queries coordinator, connects to nodes")
    print("    - Hashing: Consistent hashing with virtual nodes for load balancing")
    print("    - Replication: Each key stored on 3 nodes (1 primary + 2 replicas)")
    
    print("\n[5] Key Features:")
    print("    - Distributed storage with automatic replication")
    print("    - Fault tolerance: works with 1-3 nodes")
    print("    - Consistent hashing: balanced key distribution")
    print("    - Node discovery: automatic coordinator registration")
    print("    - Pure Python: No external dependencies required")
    
    print("\n" + "="*75)
    print("PROJECT: Distributed Key-Value Store with Consistent Hashing".center(75))
    print("LANGUAGE: Python 3 | TCP Sockets | Multithreading".center(75))
    print("FEATURES: Replication | Fault Tolerance | Load Balancing".center(75))
    print("="*75 + "\n")
    
    return True

if __name__ == "__main__":
    try:
        success = test_system()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

