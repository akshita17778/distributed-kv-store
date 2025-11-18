#!/usr/bin/env python3
"""
Test script for the Distributed Key-Value Store.
Runs automated tests to verify functionality.
"""

import subprocess
import time
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from client.client import Client


def test_basic_operations():
    """Test basic PUT, GET, DELETE operations."""
    print("\n" + "="*50)
    print("TEST 1: Basic Operations (PUT, GET, DELETE)")
    print("="*50)
    
    client = Client(coordinator_host='127.0.0.1', coordinator_port=5000)
    
    # Test PUT
    print("\n[Test] PUT key1 = value1")
    success = client.put("key1", "value1")
    if not success:
        print("❌ PUT failed")
        return False
    print("✅ PUT succeeded")
    
    # Test GET
    print("\n[Test] GET key1")
    value = client.get("key1")
    if value != "value1":
        print(f"❌ GET failed: expected 'value1', got '{value}'")
        return False
    print("✅ GET succeeded")
    
    # Test DELETE
    print("\n[Test] DELETE key1")
    success = client.delete("key1")
    if not success:
        print("❌ DELETE failed")
        return False
    print("✅ DELETE succeeded")
    
    # Verify deletion
    print("\n[Test] Verify key1 is deleted (GET should return NOT_FOUND)")
    value = client.get("key1")
    if value is not None:
        print(f"❌ Verification failed: key1 still exists with value '{value}'")
        return False
    print("✅ Verification succeeded: key1 is deleted")
    
    return True


def test_multiple_keys():
    """Test storing and retrieving multiple keys."""
    print("\n" + "="*50)
    print("TEST 2: Multiple Keys")
    print("="*50)
    
    client = Client(coordinator_host='127.0.0.1', coordinator_port=5000)
    
    test_data = {
        "user:1": "Alice",
        "user:2": "Bob",
        "user:3": "Charlie",
        "cache:123": "cache_value_456",
        "session:xyz": "session_data"
    }
    
    # Store all keys
    print("\n[Test] Storing multiple keys...")
    for key, value in test_data.items():
        print(f"  PUT {key} = {value}")
        success = client.put(key, value)
        if not success:
            print(f"❌ Failed to store {key}")
            return False
    print("✅ All keys stored")
    
    # Retrieve all keys
    print("\n[Test] Retrieving multiple keys...")
    for key, expected_value in test_data.items():
        print(f"  GET {key}")
        value = client.get(key)
        if value != expected_value:
            print(f"❌ Retrieved wrong value for {key}: expected '{expected_value}', got '{value}'")
            return False
    print("✅ All keys retrieved correctly")
    
    return True


def test_consistent_hashing():
    """Test that consistent hashing distributes keys."""
    print("\n" + "="*50)
    print("TEST 3: Consistent Hashing Distribution")
    print("="*50)
    
    from hashing import ConsistentHashRing
    
    ring = ConsistentHashRing()
    
    # Add nodes
    print("\n[Test] Adding nodes to ring...")
    nodes = ["node1:5001", "node2:5002", "node3:5003"]
    for node in nodes:
        ring.add_node(node)
    print(f"✅ Added {len(nodes)} nodes")
    
    # Test key distribution
    print("\n[Test] Checking key distribution...")
    keys = [f"key:{i}" for i in range(100)]
    distribution = {}
    
    for key in keys:
        node = ring.get_node(key)
        if node not in distribution:
            distribution[node] = 0
        distribution[node] += 1
    
    print("Distribution:")
    for node, count in sorted(distribution.items()):
        percentage = (count / len(keys)) * 100
        print(f"  {node}: {count} keys ({percentage:.1f}%)")
    
    # Check that distribution is relatively balanced (not all on one node)
    min_keys = min(distribution.values())
    max_keys = max(distribution.values())
    
    if min_keys == 0:
        print("❌ Some nodes have 0 keys (bad distribution)")
        return False
    
    if max_keys > len(keys) * 0.6:
        print("❌ Distribution is too skewed")
        return False
    
    print("✅ Distribution is reasonably balanced")
    return True


def test_replication():
    """Test that data is replicated to multiple nodes."""
    print("\n" + "="*50)
    print("TEST 4: Replication")
    print("="*50)
    
    client = Client(coordinator_host='127.0.0.1', coordinator_port=5000)
    
    print("\n[Test] Storing key with replication...")
    key = "replicated_key"
    value = "replicated_value"
    
    success = client.put(key, value)
    if not success:
        print("❌ Failed to store key")
        return False
    
    # Get nodes for this key
    nodes_info = client._get_nodes_for_key(key)
    if not nodes_info:
        print("❌ Failed to get nodes for key")
        return False
    
    primary = nodes_info["primary"]
    replicas = nodes_info["replicas"]
    
    print(f"✅ Key stored with:")
    print(f"   Primary: {primary}")
    print(f"   Replicas: {replicas}")
    
    if len(replicas) < 2:
        print(f"⚠️ Only {len(replicas)} replicas (expected 2)")
    
    # Verify we can retrieve the value
    retrieved = client.get(key)
    if retrieved != value:
        print(f"❌ Failed to retrieve replicated value")
        return False
    
    print("✅ Replicated value retrieved successfully")
    return True


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("DISTRIBUTED KEY-VALUE STORE - AUTOMATED TESTS")
    print("="*60)
    
    print("\n⚠️  Prerequisites:")
    print("  1. Coordinator should be running: python coordinator/coordinator.py")
    print("  2. At least 3 nodes should be running:")
    print("     - python node/node.py 5001")
    print("     - python node/node.py 5002")
    print("     - python node/node.py 5003")
    
    input("\nPress ENTER to continue with tests (or Ctrl+C to cancel)...")
    
    tests = [
        ("Basic Operations", test_basic_operations),
        ("Multiple Keys", test_multiple_keys),
        ("Consistent Hashing", test_consistent_hashing),
        ("Replication", test_replication),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed with error: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
        
        time.sleep(1)  # Brief delay between tests
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
