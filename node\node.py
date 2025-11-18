import socket
import threading
import time
import sys
import os
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class Node:
    """
    Node Server for the Distributed Key-Value Store.
    
    Responsibilities:
    - Store key-value pairs
    - Register itself with the coordinator
    - Handle PUT, GET, DELETE operations
    - Replicate data to replica nodes
    """
    
    def __init__(self, host='127.0.0.1', port=5001, coordinator_host='127.0.0.1', coordinator_port=5000):
        """
        Initialize a node.
        
        Args:
            host (str): Host to bind to
            port (int): Port to listen on
            coordinator_host (str): Coordinator host
            coordinator_port (int): Coordinator port
        """
        self.host = host
        self.port = port
        self.node_id = f"{host}:{port}"
        self.coordinator_host = coordinator_host
        self.coordinator_port = coordinator_port
        
        self.data = {}  # In-memory key-value store
        self.running = False
        self.lock = threading.Lock()
        self.server_socket = None
    
    def register_with_coordinator(self):
        """Register this node with the coordinator."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.coordinator_host, self.coordinator_port))
            
            command = f"REGISTER_NODE {self.host} {self.port}"
            sock.sendall(command.encode('utf-8'))
            
            response = sock.recv(1024).decode('utf-8').strip()
            print(f"[Node {self.port}] Coordinator response: {response}")
            sock.close()
            
            return True
        except Exception as e:
            print(f"[Node {self.port}] Failed to register with coordinator: {e}")
            return False
    
    def start(self):
        """Start the node server."""
        # Register with coordinator
        if not self.register_with_coordinator():
            print(f"[Node {self.port}] Failed to register, exiting")
            return
        
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.running = True
        
        print(f"[Node {self.port}] Started on {self.host}:{self.port}")
        
        try:
            while self.running:
                try:
                    client_socket, client_addr = self.server_socket.accept()
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket, client_addr),
                        daemon=True
                    )
                    client_thread.start()
                except Exception as e:
                    if self.running:
                        print(f"[Node {self.port}] Error accepting connection: {e}")
        except KeyboardInterrupt:
            print(f"\n[Node {self.port}] Shutting down...")
            self.stop()
    
    def _handle_client(self, client_socket, client_addr):
        """
        Handle a single client connection.
        
        Args:
            client_socket: The connected socket
            client_addr: Client address tuple
        """
        try:
            data = client_socket.recv(1024).decode('utf-8').strip()
            
            if not data:
                client_socket.close()
                return
            
            response = self._process_command(data)
            client_socket.sendall(response.encode('utf-8'))
        
        except Exception as e:
            print(f"[Node {self.port}] Error handling client: {e}")
        
        finally:
            client_socket.close()
    
    def _process_command(self, command):
        """
        Process a command.
        
        Args:
            command (str): Command string
        
        Returns:
            str: Response string
        """
        parts = command.split(maxsplit=2)
        
        if not parts:
            return "ERROR Invalid command"
        
        cmd = parts[0]
        
        if cmd == "PUT":
            if len(parts) < 3:
                return "ERROR Invalid PUT format"
            key, value = parts[1], parts[2]
            self._put(key, value)
            
            # Replicate to other nodes (if specified in command)
            # Format: PUT key value [replica_nodes]
            if len(parts) > 3:
                replicas = parts[3].split(',')
                self._replicate_to_nodes(key, value, replicas)
            
            return "OK"
        
        elif cmd == "GET":
            if len(parts) < 2:
                return "ERROR Invalid GET format"
            key = parts[1]
            value = self._get(key)
            if value is not None:
                return f"VALUE {value}"
            else:
                return "NOT_FOUND"
        
        elif cmd == "DELETE":
            if len(parts) < 2:
                return "ERROR Invalid DELETE format"
            key = parts[1]
            self._delete(key)
            return "OK"
        
        elif cmd == "REPLICATE":
            # Internal replication command (from primary node)
            if len(parts) < 3:
                return "ERROR Invalid REPLICATE format"
            key, value = parts[1], parts[2]
            self._put(key, value)
            return "OK"
        
        elif cmd == "INFO":
            # Return node info
            with self.lock:
                return f"OK Node {self.node_id} keys={len(self.data)}"
        
        else:
            return "ERROR Unknown command"
    
    def _put(self, key, value):
        """
        Store a key-value pair.
        
        Args:
            key (str): The key
            value (str): The value
        """
        with self.lock:
            self.data[key] = value
        print(f"[Node {self.port}] PUT {key} = {value}")
    
    def _get(self, key):
        """
        Retrieve a value by key.
        
        Args:
            key (str): The key
        
        Returns:
            str: The value, or None if not found
        """
        with self.lock:
            value = self.data.get(key)
        
        if value is not None:
            print(f"[Node {self.port}] GET {key} = {value}")
        else:
            print(f"[Node {self.port}] GET {key} = NOT_FOUND")
        
        return value
    
    def _delete(self, key):
        """
        Delete a key-value pair.
        
        Args:
            key (str): The key
        """
        with self.lock:
            if key in self.data:
                del self.data[key]
                print(f"[Node {self.port}] DELETE {key}")
            else:
                print(f"[Node {self.port}] DELETE {key} (not found)")
    
    def _replicate_to_nodes(self, key, value, replica_node_ids):
        """
        Replicate a key-value pair to replica nodes.
        
        Args:
            key (str): The key
            value (str): The value
            replica_node_ids (list): List of replica node IDs (format: "host:port")
        """
        for replica_id in replica_node_ids:
            try:
                host, port = replica_id.split(':')
                port = int(port)
                
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                sock.connect((host, port))
                
                command = f"REPLICATE {key} {value}"
                sock.sendall(command.encode('utf-8'))
                
                response = sock.recv(1024).decode('utf-8').strip()
                sock.close()
                
                if response == "OK":
                    print(f"[Node {self.port}] Replicated {key} to {replica_id}")
                else:
                    print(f"[Node {self.port}] Failed to replicate to {replica_id}: {response}")
            
            except Exception as e:
                print(f"[Node {self.port}] Error replicating to {replica_id}: {e}")
    
    def stop(self):
        """Stop the node server."""
        self.running = False
        if self.server_socket:
            self.server_socket.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Distributed KV Store Node")
    parser.add_argument('--port', type=int, required=True, help='Node port')
    parser.add_argument('--id', default=None, help='Node ID (optional)')
    parser.add_argument('--coordinator-host', default='127.0.0.1', help='Coordinator host')
    parser.add_argument('--coordinator-port', type=int, default=5000, help='Coordinator port')
    
    args = parser.parse_args()
    
    port = args.port
    coord_host = args.coordinator_host
    coord_port = args.coordinator_port
    
    node = Node(host='127.0.0.1', port=port, coordinator_host=coord_host, coordinator_port=coord_port)
    try:
        node.start()
    except KeyboardInterrupt:
        print(f"\n[Node {port}] Interrupted")
        node.stop()
