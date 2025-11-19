


echo "=========================================="
echo "Distributed Key-Value Store - Quick Start"
echo "=========================================="
echo ""
echo "This will help you start:"
echo "  1. Coordinator (port 5000)"
echo "  2. Nodes (ports 5001, 5002, 5003)"
echo "  3. Client"
echo ""
echo "Prerequisites: Python 3.7+"
echo ""

read -p "Press ENTER to continue..."

echo ""
echo "Starting Coordinator..."
echo "(Run this in a new terminal, or add '&' to background it)"
echo ""
echo "  python coordinator/coordinator.py"
echo ""

read -p "Press ENTER after starting the Coordinator..."

echo ""
echo "Starting Nodes..."
echo "(Run each in a new terminal)"
echo ""
echo "Terminal 1:"
echo "  python node/node.py 5001"
echo ""
echo "Terminal 2:"
echo "  python node/node.py 5002"
echo ""
echo "Terminal 3:"
echo "  python node/node.py 5003"
echo ""

read -p "Press ENTER after starting all 3 nodes..."

echo ""
echo "Starting Client..."
echo ""
echo "Interactive mode (recommended for testing):"
echo "  python client/client.py"
echo ""
echo "Or single command mode:"
echo "  python client/client.py --command 'PUT key value'"
echo ""

read -p "Start client? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python client/client.py
fi
