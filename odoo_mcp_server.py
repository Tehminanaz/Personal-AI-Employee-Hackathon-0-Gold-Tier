#!/usr/bin/env python3
"""
Odoo MCP Server - Digital FTE System
Provides integration with Odoo Community Edition via JSON-RPC API.

This MCP server enables the Digital FTE to:
- Create invoice drafts
- Record payment drafts
- Fetch recent transactions
- Reconcile bank statements

All operations are in DRAFT mode by default, requiring human approval
before posting to maintain financial safety.

Usage:
    from odoo_mcp_server import OdooMCPServer
    server = OdooMCPServer()
    invoice_id = server.create_invoice_draft("Client A", 500.00, "Consulting")

Requirements:
    pip install odoorpc

Environment Variables:
    ODOO_URL - Odoo instance URL (default: http://localhost:8069)
    ODOO_DB - Database name (default: odoo)
    ODOO_USERNAME - Odoo username (default: admin)
    ODOO_PASSWORD - Odoo password (required)
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any

try:
    import odoorpc
    ODOORPC_AVAILABLE = True
except ImportError:
    ODOORPC_AVAILABLE = False
    print("WARNING: odoorpc not installed. Run: pip install odoorpc")

# Configuration
BASE_DIR = Path(__file__).parent.resolve()
LOGS_DIR = BASE_DIR / "Logs"
LOGS_DIR.mkdir(exist_ok=True)

# Logging setup
LOG_FILE = LOGS_DIR / "odoo_mcp.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("OdooMCP")


class OdooMCPServer:
    """
    MCP Server for Odoo Community Edition integration.
    
    Provides safe, draft-only operations for financial management.
    All operations require human approval before posting.
    """
    
    def __init__(
        self,
        url: Optional[str] = None,
        db: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None
    ):
        """
        Initialize Odoo MCP Server.
        
        Args:
            url: Odoo instance URL (default: from ODOO_URL env var)
            db: Database name (default: from ODOO_DB env var)
            username: Odoo username (default: from ODOO_USERNAME env var)
            password: Odoo password (default: from ODOO_PASSWORD env var)
        """
        if not ODOORPC_AVAILABLE:
            raise ImportError("odoorpc library not available. Install with: pip install odoorpc")
        
        # Load configuration from environment variables
        self.url = url or os.getenv("ODOO_URL", "http://localhost:8069")
        self.db = db or os.getenv("ODOO_DB", "odoo")
        self.username = username or os.getenv("ODOO_USERNAME", "admin")
        self.password = password or os.getenv("ODOO_PASSWORD")
        
        if not self.password:
            raise ValueError("ODOO_PASSWORD environment variable is required")
        
        # Parse URL to get host and port
        from urllib.parse import urlparse
        parsed = urlparse(self.url)
        self.host = parsed.hostname or "localhost"
        self.port = parsed.port or 8069
        self.protocol = "jsonrpc+ssl" if parsed.scheme == "https" else "jsonrpc"
        
        self.odoo = None
        self._connect()
    
    def _connect(self) -> None:
        """Establish connection to Odoo instance."""
        try:
            logger.info(f"Connecting to Odoo at {self.host}:{self.port}")
            self.odoo = odoorpc.ODOO(self.host, protocol=self.protocol, port=self.port)
            self.odoo.login(self.db, self.username, self.password)
            logger.info(f"Successfully connected to Odoo as {self.username}")
        except Exception as e:
            logger.error(f"Failed to connect to Odoo: {e}")
            raise
    
    def test_connection(self) -> bool:
        """
        Test connection to Odoo instance.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Try to access partner model as connection test
            Partner = self.odoo.env['res.partner']
            count = Partner.search_count([])
            logger.info(f"Connection test successful. Found {count} partners.")
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def create_invoice_draft(
        self,
        partner_name: str,
        amount: float,
        description: str,
        invoice_date: Optional[str] = None
    ) -> Optional[int]:
        """
        Create an invoice draft in Odoo.
        
        Args:
            partner_name: Customer/partner name
            amount: Invoice amount
            description: Invoice description/reference
            invoice_date: Invoice date (YYYY-MM-DD format, default: today)
        
        Returns:
            Invoice ID if successful, None otherwise
        """
        try:
            logger.info(f"Creating invoice draft for {partner_name}: ${amount}")
            
            # Get or create partner
            Partner = self.odoo.env['res.partner']
            partner_ids = Partner.search([('name', '=', partner_name)])
            
            if not partner_ids:
                logger.info(f"Partner '{partner_name}' not found, creating...")
                partner_id = Partner.create({'name': partner_name})
            else:
                partner_id = partner_ids[0]
            
            # Get default product for service
            Product = self.odoo.env['product.product']
            product_ids = Product.search([('name', '=', 'Service')], limit=1)
            
            if not product_ids:
                logger.warning("Default 'Service' product not found, creating...")
                product_id = Product.create({
                    'name': 'Service',
                    'type': 'service',
                    'list_price': amount
                })
            else:
                product_id = product_ids[0]
            
            # Create invoice
            Invoice = self.odoo.env['account.move']
            invoice_vals = {
                'partner_id': partner_id,
                'move_type': 'out_invoice',
                'invoice_date': invoice_date or datetime.now().strftime('%Y-%m-%d'),
                'ref': description,
                'invoice_line_ids': [(0, 0, {
                    'product_id': product_id,
                    'name': description,
                    'quantity': 1,
                    'price_unit': amount
                })]
            }
            
            invoice_id = Invoice.create(invoice_vals)
            logger.info(f"Invoice draft created successfully. ID: {invoice_id}")
            
            return invoice_id
            
        except Exception as e:
            logger.error(f"Failed to create invoice draft: {e}", exc_info=True)
            return None
    
    def record_payment_draft(
        self,
        invoice_id: int,
        amount: float,
        payment_method: str = "manual",
        payment_date: Optional[str] = None
    ) -> Optional[int]:
        """
        Record a payment draft for an invoice.
        
        Args:
            invoice_id: Invoice ID to pay
            amount: Payment amount
            payment_method: Payment method (manual, bank, etc.)
            payment_date: Payment date (YYYY-MM-DD format, default: today)
        
        Returns:
            Payment ID if successful, None otherwise
        """
        try:
            logger.info(f"Recording payment draft for invoice {invoice_id}: ${amount}")
            
            # Get invoice
            Invoice = self.odoo.env['account.move']
            invoice = Invoice.browse(invoice_id)
            
            if not invoice:
                logger.error(f"Invoice {invoice_id} not found")
                return None
            
            # Create payment
            Payment = self.odoo.env['account.payment']
            payment_vals = {
                'payment_type': 'inbound',
                'partner_type': 'customer',
                'partner_id': invoice.partner_id.id,
                'amount': amount,
                'date': payment_date or datetime.now().strftime('%Y-%m-%d'),
                'ref': f"Payment for {invoice.name}",
                'journal_id': 1  # Default journal, should be configured
            }
            
            payment_id = Payment.create(payment_vals)
            logger.info(f"Payment draft created successfully. ID: {payment_id}")
            
            return payment_id
            
        except Exception as e:
            logger.error(f"Failed to record payment draft: {e}", exc_info=True)
            return None
    
    def fetch_recent_transactions(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Fetch recent transactions from Odoo.
        
        Args:
            days: Number of days to look back (default: 7)
        
        Returns:
            List of transaction dictionaries
        """
        try:
            logger.info(f"Fetching transactions from last {days} days")
            
            from datetime import timedelta
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            # Fetch invoices
            Invoice = self.odoo.env['account.move']
            invoice_ids = Invoice.search([
                ('invoice_date', '>=', start_date),
                ('move_type', 'in', ['out_invoice', 'in_invoice'])
            ])
            
            transactions = []
            for invoice_id in invoice_ids:
                invoice = Invoice.browse(invoice_id)
                transactions.append({
                    'id': invoice.id,
                    'type': 'invoice',
                    'date': invoice.invoice_date,
                    'partner': invoice.partner_id.name,
                    'amount': invoice.amount_total,
                    'state': invoice.state,
                    'reference': invoice.ref or invoice.name
                })
            
            logger.info(f"Found {len(transactions)} transactions")
            return transactions
            
        except Exception as e:
            logger.error(f"Failed to fetch transactions: {e}", exc_info=True)
            return []
    
    def get_account_balance(self, account_code: str) -> Optional[float]:
        """
        Get current balance of an account.
        
        Args:
            account_code: Account code (e.g., '100000' for bank)
        
        Returns:
            Account balance if successful, None otherwise
        """
        try:
            logger.info(f"Fetching balance for account {account_code}")
            
            Account = self.odoo.env['account.account']
            account_ids = Account.search([('code', '=', account_code)])
            
            if not account_ids:
                logger.error(f"Account {account_code} not found")
                return None
            
            account = Account.browse(account_ids[0])
            balance = account.current_balance
            
            logger.info(f"Account {account_code} balance: ${balance}")
            return balance
            
        except Exception as e:
            logger.error(f"Failed to get account balance: {e}", exc_info=True)
            return None


def main():
    """Test the Odoo MCP Server."""
    print("=" * 80)
    print("Odoo MCP Server - Connection Test")
    print("=" * 80)
    
    try:
        server = OdooMCPServer()
        
        # Test connection
        if server.test_connection():
            print("✅ Connection successful!")
            
            # Test invoice creation
            print("\nTesting invoice draft creation...")
            invoice_id = server.create_invoice_draft(
                partner_name="Test Client",
                amount=100.00,
                description="Test invoice from MCP server"
            )
            
            if invoice_id:
                print(f"✅ Invoice draft created! ID: {invoice_id}")
            else:
                print("❌ Failed to create invoice draft")
            
            # Test transaction fetch
            print("\nFetching recent transactions...")
            transactions = server.fetch_recent_transactions(days=30)
            print(f"✅ Found {len(transactions)} transactions")
            
            for txn in transactions[:5]:  # Show first 5
                print(f"  - {txn['date']}: {txn['partner']} - ${txn['amount']} ({txn['state']})")
        else:
            print("❌ Connection failed!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("=" * 80)


if __name__ == "__main__":
    main()
