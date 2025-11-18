import hashlib
import bisect


class ConsistentHashRing:
    """
    Consistent Hashing Ring for distributed key-value store.
    
    Uses SHA-256 hashing and virtual nodes for better distribution.
    Each physical node creates VIRTUAL_NODES virtual nodes on the ring.
    """
    
    VIRTUAL_NODES = 3  # Number of virtual nodes per physical node
    
    def __init__(self):
        """Initialize an empty hash ring."""
        self.ring = {}  # hash_value -> node_id
        self.sorted_keys = []  # sorted list of hash values for binary search
        self.nodes = set()  # set of physical node ids
    
    def _hash(self, key):
        """
        Hash a key/node using SHA-256.
        
        Args:
            key (str): The key or node identifier to hash
        
        Returns:
            int: Integer hash value
        """
        hash_obj = hashlib.sha256(key.encode('utf-8'))
        return int(hash_obj.hexdigest(), 16)
    
    def add_node(self, node_id):
        """
        Add a physical node to the ring.
        Creates VIRTUAL_NODES virtual nodes for this physical node.
        
        Args:
            node_id (str): Unique identifier for the node (e.g., "host:port")
        """
        if node_id in self.nodes:
            return  # Node already exists
        
        self.nodes.add(node_id)
        
        # Add virtual nodes
        for i in range(self.VIRTUAL_NODES):
            virtual_key = f"{node_id}:virtual:{i}"
            hash_value = self._hash(virtual_key)
            self.ring[hash_value] = node_id
        
        # Re-sort the ring keys for binary search
        self.sorted_keys = sorted(self.ring.keys())
    
    def remove_node(self, node_id):
        """
        Remove a physical node from the ring.
        Removes all virtual nodes associated with this physical node.
        
        Args:
            node_id (str): Unique identifier for the node
        """
        if node_id not in self.nodes:
            return  # Node doesn't exist
        
        self.nodes.discard(node_id)
        
        # Remove all virtual nodes for this physical node
        hash_values_to_remove = [
            h for h in self.ring if self.ring[h] == node_id
        ]
        for h in hash_values_to_remove:
            del self.ring[h]
        
        # Re-sort the ring keys
        self.sorted_keys = sorted(self.ring.keys())
    
    def get_node(self, key):
        """
        Get the node responsible for a key.
        Uses consistent hashing: find the first node clockwise on the ring.
        
        Args:
            key (str): The key to look up
        
        Returns:
            str: Node ID (physical node identifier)
        
        Raises:
            ValueError: If the ring is empty
        """
        if not self.ring:
            raise ValueError("Ring is empty, no nodes available")
        
        hash_value = self._hash(key)
        
        # Find the first node with hash >= key hash (clockwise)
        idx = bisect.bisect_right(self.sorted_keys, hash_value)
        
        # If we're past the end, wrap around to the beginning
        if idx == len(self.sorted_keys):
            idx = 0
        
        return self.ring[self.sorted_keys[idx]]
    
    def get_nodes(self, key, count=3):
        """
        Get N nodes responsible for a key (for replication).
        Returns the key's primary node + (count-1) replicas.
        
        Args:
            key (str): The key to look up
            count (int): Number of nodes to return (default 3: 1 primary + 2 replicas)
        
        Returns:
            list: List of node IDs, starting with primary
        
        Raises:
            ValueError: If the ring has fewer nodes than requested
        """
        if not self.ring:
            raise ValueError("Ring is empty, no nodes available")
        
        if len(self.nodes) < count:
            # Return all unique nodes available
            count = len(self.nodes)
        
        hash_value = self._hash(key)
        idx = bisect.bisect_right(self.sorted_keys, hash_value)
        
        if idx == len(self.sorted_keys):
            idx = 0
        
        nodes = []
        seen = set()
        
        # Collect unique physical nodes starting from idx
        for i in range(len(self.sorted_keys)):
            current_idx = (idx + i) % len(self.sorted_keys)
            node_id = self.ring[self.sorted_keys[current_idx]]
            
            if node_id not in seen:
                nodes.append(node_id)
                seen.add(node_id)
                if len(nodes) == count:
                    break
        
        return nodes
    
    def get_all_nodes(self):
        """
        Get all physical nodes in the ring.
        
        Returns:
            list: List of unique node IDs
        """
        return sorted(list(self.nodes))
