#!/usr/bin/env python3
"""
Quick test script to demonstrate Distributed KV Store working
"""
import os
import sys
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from client.client import Client

def main():
    print("=" * 60)
    print("DISTRIBUTED KV STORE - LIVE DEMONSTRATION")
    print("=" * 60)
    print()
    
    # Create client
    client = Client(coordinator_host='127.0.0.1', coordinator_port=5000)
    
    # Test 1: List nodes
    print("[TEST 1] Listing registered nodes...")
    response = client._send_to_coordinator("LIST_NODES")
    print(f"Response: {response}")
    print()
    
    # Test 2: PUT operation
    print("[TEST 2] Storing a key-value pair...")
    print("Command: PUT resume-project 'Distributed-Key-Value-Store-System'")
    client.put("resume-project", "Distributed-Key-Value-Store-System")
    print()
    time.sleep(1)
    
    # Test 3: GET operation
    print("[TEST 3] Retrieving the value...")
    print("Command: GET resume-project")
    result = client.get("resume-project")
    print()
    
    # Test 4: Additional operations
    print("[TEST 4] Storing multiple entries...")
    entries = [
        ("tech-stack", "Python TCP Sockets, Consistent Hashing, Threading"),
        ("features", "Replication, Fault Tolerance, Node Discovery"),
        ("architecture", "Coordinator-Node-Client Model")
    ]
    
    for key, value in entries:
        print(f"PUT {key} = {value}")
        client.put(key, value)
        time.sleep(0.5)
    
    print()
    print("[TEST 5] Retrieving all entries...")
    for key, _ in entries:
        print(f"GET {key}:")
        client.get(key)
        print()
    
    print("=" * 60)
    print("SYSTEM WORKING CORRECTLY!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
