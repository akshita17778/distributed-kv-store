import socket
import threading
import time
import sys
import os

# Add parent directory to path so we can import hashing
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hashing import ConsistentHashRing


class Coordinator:
    """
    Coordinator Server for the Distributed Key-Value Store.
    
    Responsibilities:
    - Maintain a consistent hash ring of all nodes
    - Register/unregister nodes
    - Return primary + replica nodes for a given key
    - Detect node failures via heartbeat (ping)
    """
    
    def __init__(self, host='127.0.0.1', port=5000):
        """
        Initialize the coordinator.
        
        Args:
            host (str): Host to bind to
            port (int): Port to listen on
        """
        self.host = host
        self.port = port
        self.ring = ConsistentHashRing()
        self.nodes = {}  # node_id -> {"host": h, "port": p, "last_heartbeat": time}
        self.running = False
        self.lock = threading.Lock()
        self.server_socket = None
    
    def start(self):
        """Start the coordinator server."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.running = True
        
        print(f"[Coordinator] Started on {self.host}:{self.port}")
        
        # Start heartbeat thread
        heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        heartbeat_thread.start()
        
        # Accept client connections
        try:
            while self.running:
                try:
                    client_socket, client_addr = self.server_socket.accept()
                    # Handle each client in a separate thread
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket, client_addr),
                        daemon=True
                    )
                    client_thread.start()
                except Exception as e:
                    if self.running:
                        print(f"[Coordinator] Error accepting connection: {e}")
        except KeyboardInterrupt:
            print("\n[Coordinator] Shutting down...")
            self.stop()
    
    def _handle_client(self, client_socket, client_addr):
        """
        Handle a single client connection.
        
        Args:
            client_socket: The connected socket
            client_addr: Client address tuple
        """
        try:
            # Receive the command
            data = client_socket.recv(1024).decode('utf-8').strip()
            
            if not data:
                client_socket.close()
                return
            
            response = self._process_command(data)
            client_socket.sendall(response.encode('utf-8'))
        
        except Exception as e:
            print(f"[Coordinator] Error handling client {client_addr}: {e}")
        
        finally:
            client_socket.close()
    
    def _process_command(self, command):
        """
        Process a coordinator command.
        
        Args:
            command (str): Command string
        
        Returns:
            str: Response string
        """
        parts = command.split()
        
        if not parts:
            return "ERROR Invalid command"
        
        cmd = parts[0]
        
        if cmd == "REGISTER_NODE":
            # REGISTER_NODE host port
            if len(parts) < 3:
                return "ERROR Invalid REGISTER_NODE format"
            return self._register_node(parts[1], parts[2])
        
        elif cmd == "UNREGISTER_NODE":
            # UNREGISTER_NODE host port
            if len(parts) < 3:
                return "ERROR Invalid UNREGISTER_NODE format"
            return self._unregister_node(parts[1], parts[2])
        
        elif cmd == "GET_NODES_FOR_KEY":
            # GET_NODES_FOR_KEY key
            if len(parts) < 2:
                return "ERROR Invalid GET_NODES_FOR_KEY format"
            return self._get_nodes_for_key(parts[1])
        
        elif cmd == "LIST_NODES":
            # LIST_NODES
            return self._list_nodes()
        
        else:
            return "ERROR Unknown command"
    
    def _register_node(self, host, port):
        """
        Register a new node.
        
        Args:
            host (str): Node host
            port (str): Node port
        
        Returns:
            str: Response message
        """
        node_id = f"{host}:{port}"
        
        with self.lock:
            if node_id in self.nodes:
                return f"WARNING Node {node_id} already registered"
            
            self.nodes[node_id] = {
                "host": host,
                "port": int(port),
                "last_heartbeat": time.time()
            }
            self.ring.add_node(node_id)
            print(f"[Coordinator] Node registered: {node_id}")
        
        return f"OK Node {node_id} registered"
    
    def _unregister_node(self, host, port):
        """
        Unregister a node.
        
        Args:
            host (str): Node host
            port (str): Node port
        
        Returns:
            str: Response message
        """
        node_id = f"{host}:{port}"
        
        with self.lock:
            if node_id not in self.nodes:
                return f"ERROR Node {node_id} not found"
            
            del self.nodes[node_id]
            self.ring.remove_node(node_id)
            print(f"[Coordinator] Node unregistered: {node_id}")
        
        return f"OK Node {node_id} unregistered"
    
    def _get_nodes_for_key(self, key):
        """
        Get primary + replica nodes for a key.
        
        Args:
            key (str): The key
        
        Returns:
            str: Response with primary and replica nodes
        """
        try:
            with self.lock:
                nodes = self.ring.get_nodes(key, count=3)
            
            if not nodes:
                return "ERROR No nodes available"
            
            response = f"PRIMARY {nodes[0]}"
            for i in range(1, len(nodes)):
                response += f"\nREPLICA {nodes[i]}"
            
            return response
        
        except Exception as e:
            return f"ERROR {str(e)}"
    
    def _list_nodes(self):
        """
        List all registered nodes.
        
        Returns:
            str: Response with list of nodes
        """
        with self.lock:
            if not self.nodes:
                return "OK No nodes registered"
            
            response = "OK Nodes:\n"
            for node_id in sorted(self.nodes.keys()):
                response += f"  {node_id}\n"
            
            return response.strip()
    
    def _heartbeat_loop(self):
        """
        Periodically check if nodes are alive.
        Remove dead nodes from the ring.
        """
        while self.running:
            time.sleep(5)  # Check every 5 seconds
            
            with self.lock:
                dead_nodes = []
                for node_id, node_info in self.nodes.items():
                    # If no heartbeat in 10 seconds, mark as dead
                    if time.time() - node_info['last_heartbeat'] > 10:
                        dead_nodes.append(node_id)
                
                for node_id in dead_nodes:
                    host, port = node_id.split(':')
                    self._unregister_node(host, port)
                    print(f"[Coordinator] Node {node_id} marked as dead and removed")
    
    def stop(self):
        """Stop the coordinator server."""
        self.running = False
        if self.server_socket:
            self.server_socket.close()


if __name__ == "__main__":
    coordinator = Coordinator(host='127.0.0.1', port=5000)
    try:
        coordinator.start()
    except KeyboardInterrupt:
        print("\n[Coordinator] Interrupted")
        coordinator.stop()
