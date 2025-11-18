import socket
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class Client:
    """
    Client for the Distributed Key-Value Store.
    
    Workflow:
    1. Connect to coordinator and ask which nodes store a key
    2. Connect directly to the primary node for PUT/GET/DELETE
    3. Coordinator returns: primary node + 2 replicas
    """
    
    def __init__(self, coordinator_host='127.0.0.1', coordinator_port=5000):
        """
        Initialize the client.
        
        Args:
            coordinator_host (str): Coordinator host
            coordinator_port (int): Coordinator port
        """
        self.coordinator_host = coordinator_host
        self.coordinator_port = coordinator_port
    
    def _send_to_coordinator(self, command):
        """
        Send a command to the coordinator.
        
        Args:
            command (str): Command to send
        
        Returns:
            str: Response from coordinator
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((self.coordinator_host, self.coordinator_port))
            
            sock.sendall(command.encode('utf-8'))
            response = sock.recv(4096).decode('utf-8').strip()
            sock.close()
            
            return response
        except Exception as e:
            print(f"[Client] Error communicating with coordinator: {e}")
            return None
    
    def _get_nodes_for_key(self, key):
        """
        Query the coordinator for nodes responsible for a key.
        
        Args:
            key (str): The key
        
        Returns:
            dict: {"primary": "host:port", "replicas": ["host:port", ...]} or None on error
        """
        command = f"GET_NODES_FOR_KEY {key}"
        response = self._send_to_coordinator(command)
        
        if not response or response.startswith("ERROR"):
            print(f"[Client] Coordinator error: {response}")
            return None
        
        lines = response.split('\n')
        result = {"primary": None, "replicas": []}
        
        for line in lines:
            parts = line.split()
            if len(parts) >= 2:
                if parts[0] == "PRIMARY":
                    result["primary"] = parts[1]
                elif parts[0] == "REPLICA":
                    result["replicas"].append(parts[1])
        
        return result if result["primary"] else None
    
    def _send_to_node(self, host, port, command):
        """
        Send a command to a node.
        
        Args:
            host (str): Node host
            port (str): Node port
            command (str): Command to send
        
        Returns:
            str: Response from node
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((host, int(port)))
            
            sock.sendall(command.encode('utf-8'))
            response = sock.recv(4096).decode('utf-8').strip()
            sock.close()
            
            return response
        except Exception as e:
            print(f"[Client] Error communicating with node {host}:{port}: {e}")
            return None
    
    def put(self, key, value):
        """
        Store a key-value pair in the distributed store.
        
        Args:
            key (str): The key
            value (str): The value
        
        Returns:
            bool: True if successful, False otherwise
        """
        # Get nodes from coordinator
        nodes_info = self._get_nodes_for_key(key)
        if not nodes_info:
            print("[Client] Failed to get nodes for key")
            return False
        
        primary = nodes_info["primary"]
        replicas = nodes_info["replicas"]
        
        # Send PUT to primary
        host, port = primary.split(':')
        
        # Include replica nodes in the command so primary can replicate
        replicas_str = ','.join(replicas) if replicas else ""
        if replicas_str:
            command = f"PUT {key} {value} {replicas_str}"
        else:
            command = f"PUT {key} {value}"
        
        response = self._send_to_node(host, port, command)
        
        if response == "OK":
            print(f"[Client] PUT {key} = {value} [primary: {primary}, replicas: {replicas}]")
            return True
        else:
            print(f"[Client] PUT failed: {response}")
            return False
    
    def get(self, key):
        """
        Retrieve a value from the distributed store.
        
        Args:
            key (str): The key
        
        Returns:
            str: The value, or None if not found
        """
        # Get nodes from coordinator
        nodes_info = self._get_nodes_for_key(key)
        if not nodes_info:
            print("[Client] Failed to get nodes for key")
            return None
        
        primary = nodes_info["primary"]
        replicas = nodes_info["replicas"]
        
        # Try primary first
        host, port = primary.split(':')
        command = f"GET {key}"
        response = self._send_to_node(host, port, command)
        
        if response and response.startswith("VALUE"):
            value = response[6:].strip()  # Remove "VALUE " prefix
            print(f"[Client] GET {key} = {value}")
            return value
        
        # If primary fails, try replicas
        if response and response == "NOT_FOUND":
            print(f"[Client] GET {key}: NOT_FOUND")
            return None
        
        print(f"[Client] Primary node failed, trying replicas...")
        for replica in replicas:
            host, port = replica.split(':')
            response = self._send_to_node(host, port, command)
            
            if response and response.startswith("VALUE"):
                value = response[6:].strip()
                print(f"[Client] GET {key} = {value} (from replica {replica})")
                return value
        
        print(f"[Client] GET {key}: NOT_FOUND (from all replicas)")
        return None
    
    def delete(self, key):
        """
        Delete a key-value pair from the distributed store.
        
        Args:
            key (str): The key
        
        Returns:
            bool: True if successful, False otherwise
        """
        # Get nodes from coordinator
        nodes_info = self._get_nodes_for_key(key)
        if not nodes_info:
            print("[Client] Failed to get nodes for key")
            return False
        
        primary = nodes_info["primary"]
        
        # Send DELETE to primary
        host, port = primary.split(':')
        command = f"DELETE {key}"
        response = self._send_to_node(host, port, command)
        
        if response == "OK":
            print(f"[Client] DELETE {key} [primary: {primary}]")
            return True
        else:
            print(f"[Client] DELETE failed: {response}")
            return False
    
    def interactive_shell(self):
        """Run an interactive shell for the client."""
        print("\n=== Distributed KV Store Client ===")
        print("Commands:")
        print("  PUT key value     - Store a key-value pair")
        print("  GET key           - Retrieve a value")
        print("  DELETE key        - Delete a key-value pair")
        print("  LIST_NODES        - List all registered nodes")
        print("  EXIT              - Exit the shell")
        print("=" * 35 + "\n")
        
        while True:
            try:
                user_input = input(">> ").strip()
                
                if not user_input:
                    continue
                
                parts = user_input.split(maxsplit=2)
                cmd = parts[0].upper()
                
                if cmd == "EXIT":
                    print("Goodbye!")
                    break
                
                elif cmd == "PUT":
                    if len(parts) < 3:
                        print("Usage: PUT key value")
                        continue
                    self.put(parts[1], parts[2])
                
                elif cmd == "GET":
                    if len(parts) < 2:
                        print("Usage: GET key")
                        continue
                    self.get(parts[1])
                
                elif cmd == "DELETE":
                    if len(parts) < 2:
                        print("Usage: DELETE key")
                        continue
                    self.delete(parts[1])
                
                elif cmd == "LIST_NODES":
                    response = self._send_to_coordinator("LIST_NODES")
                    print(response)
                
                else:
                    print(f"Unknown command: {cmd}")
            
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Distributed KV Store Client")
    parser.add_argument('--host', default='127.0.0.1', help='Coordinator host')
    parser.add_argument('--port', type=int, default=5000, help='Coordinator port')
    parser.add_argument('--command', help='Single command to execute (e.g., "PUT key value")')
    
    args = parser.parse_args()
    
    client = Client(coordinator_host=args.host, coordinator_port=args.port)
    
    if args.command:
        # Execute single command
        parts = args.command.split(maxsplit=2)
        cmd = parts[0].upper()
        
        if cmd == "PUT" and len(parts) >= 3:
            client.put(parts[1], parts[2])
        elif cmd == "GET" and len(parts) >= 2:
            client.get(parts[1])
        elif cmd == "DELETE" and len(parts) >= 2:
            client.delete(parts[1])
        elif cmd == "LIST_NODES":
            response = client._send_to_coordinator("LIST_NODES")
            print(response)
        else:
            print("Usage: --command 'PUT key value' | --command 'GET key' | --command 'DELETE key' | --command 'LIST_NODES'")
    else:
        # Interactive shell
        client.interactive_shell()
