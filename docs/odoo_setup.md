# Odoo Community Edition - Setup Guide

## Overview
This guide walks you through installing and configuring Odoo Community Edition for integration with the Digital FTE system.

**Odoo Version:** 19+ (recommended for JSON-RPC API compatibility)
**Installation Method:** Docker (recommended) or Native

---

## Method 1: Docker Installation (Recommended)

### Prerequisites
- Docker Desktop installed on Windows
- At least 4GB RAM available
- 10GB free disk space

### Step 1: Create Docker Compose File

Create `docker-compose.yml` in your project directory:

```yaml
version: '3.8'
services:
  odoo:
    image: odoo:19
    container_name: odoo_community
    ports:
      - "8069:8069"
    environment:
      - HOST=db
      - USER=odoo
      - PASSWORD=odoo_password_2026
    volumes:
      - odoo-data:/var/lib/odoo
      - ./config:/etc/odoo
    depends_on:
      - db
    restart: unless-stopped
  
  db:
    image: postgres:15
    container_name: odoo_postgres
    environment:
      - POSTGRES_DB=postgres
      - POSTGRES_USER=odoo
      - POSTGRES_PASSWORD=odoo_password_2026
    volumes:
      - db-data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  odoo-data:
  db-data:
```

### Step 2: Start Odoo

```bash
# Navigate to project directory
cd "c:\Users\Kashan\Documents\Digital labor\digital_labor2 - Copy"

# Start Odoo
docker-compose up -d

# Check logs
docker-compose logs -f odoo
```

### Step 3: Initial Setup

1. Open browser: `http://localhost:8069`
2. Create database:
   - **Database Name:** `odoo`
   - **Email:** your email
   - **Password:** strong password (save this!)
   - **Language:** English
   - **Country:** Your country
3. Click "Create Database"
4. Wait 2-3 minutes for setup to complete

### Step 4: Configure Company

1. Go to **Settings** → **General Settings**
2. Under **Companies**, click "Update Info"
3. Fill in:
   - **Company Name:** Your business name
   - **Currency:** USD (or your currency)
   - **Timezone:** Your timezone

### Step 5: Install Accounting Module

1. Go to **Apps**
2. Search for "Accounting"
3. Click **Install**
4. Wait for installation to complete

### Step 6: Configure Chart of Accounts

1. Go to **Accounting** → **Configuration** → **Chart of Accounts**
2. Verify default accounts are created
3. Common accounts:
   - `100000` - Bank
   - `400000` - Revenue
   - `600000` - Expenses

---

## Method 2: Native Installation (Windows)

### Prerequisites
- Python 3.10 or 3.11 (NOT 3.12+, Odoo compatibility issue)
- PostgreSQL 15
- Git

### Step 1: Install PostgreSQL

1. Download PostgreSQL 15 from: https://www.postgresql.org/download/windows/
2. Run installer, set password for `postgres` user
3. Add PostgreSQL to PATH: `C:\Program Files\PostgreSQL\15\bin`

### Step 2: Create Odoo Database

```bash
# Open Command Prompt as Administrator
psql -U postgres

# In PostgreSQL prompt:
CREATE USER odoo WITH PASSWORD 'odoo_password_2026';
CREATE DATABASE odoo OWNER odoo;
\q
```

### Step 3: Install Odoo

```bash
# Clone Odoo repository
git clone https://github.com/odoo/odoo.git --depth 1 --branch 19.0 C:\odoo

# Install Python dependencies
cd C:\odoo
pip install -r requirements.txt

# Install additional Windows dependencies
pip install psycopg2-binary
```

### Step 4: Create Odoo Configuration

Create `C:\odoo\odoo.conf`:

```ini
[options]
admin_passwd = admin_master_password_2026
db_host = localhost
db_port = 5432
db_user = odoo
db_password = odoo_password_2026
addons_path = C:\odoo\addons
http_port = 8069
```

### Step 5: Start Odoo

```bash
cd C:\odoo
python odoo-bin -c odoo.conf
```

### Step 6: Access Odoo

1. Open browser: `http://localhost:8069`
2. Follow initial setup steps from Method 1, Step 3

---

## API Access Configuration

### Step 1: Enable API Access

1. Go to **Settings** → **Technical** → **Database Structure** → **Models**
2. Verify `account.move` (Invoices) and `account.payment` (Payments) models exist

### Step 2: Create API User (Recommended)

1. Go to **Settings** → **Users & Companies** → **Users**
2. Click **Create**
3. Fill in:
   - **Name:** Digital FTE API
   - **Email:** fte@yourdomain.com
   - **Access Rights:** Accounting / Manager
4. Save and set password

### Step 3: Configure Environment Variables

Add to your `.env` file:

```bash
# Odoo Configuration
ODOO_URL=http://localhost:8069
ODOO_DB=odoo
ODOO_USERNAME=admin
ODOO_PASSWORD=your_odoo_password_here
```

**Security Note:** Never commit `.env` to Git!

---

## Testing the Integration

### Step 1: Install Python Dependencies

```bash
# In your project directory
pip install odoorpc
```

### Step 2: Test Connection

```bash
python odoo_mcp_server.py
```

**Expected Output:**
```
================================================================================
Odoo MCP Server - Connection Test
================================================================================
Connecting to Odoo at localhost:8069
Successfully connected to Odoo as admin
Connection test successful. Found X partners.
✅ Connection successful!

Testing invoice draft creation...
Invoice draft created successfully. ID: 1
✅ Invoice draft created! ID: 1

Fetching recent transactions...
✅ Found 1 transactions
  - 2026-01-19: Test Client - $100.0 (draft)
================================================================================
```

### Step 3: Verify in Odoo UI

1. Go to **Accounting** → **Customers** → **Invoices**
2. You should see "Test invoice from MCP server" in draft state
3. Click on it to view details

---

## Troubleshooting

### Issue: "Connection refused" error

**Solution:**
```bash
# Check if Odoo is running
docker ps  # For Docker installation
# OR
netstat -an | findstr 8069  # Check if port 8069 is listening
```

### Issue: "Authentication failed" error

**Solution:**
- Verify credentials in `.env` file
- Try logging in via web UI with same credentials
- Check database name is correct

### Issue: "Module not found: odoorpc"

**Solution:**
```bash
pip install odoorpc
```

### Issue: Docker container keeps restarting

**Solution:**
```bash
# Check logs
docker-compose logs odoo

# Common fix: Increase Docker memory
# Docker Desktop → Settings → Resources → Memory: 4GB minimum
```

---

## Next Steps

1. ✅ Odoo installed and running
2. ✅ API access configured
3. ✅ Test connection successful
4. → Integrate with `action_executor.py`
5. → Create Odoo accountant skill
6. → Test invoice workflow end-to-end

---

## Resources

- **Odoo Documentation:** https://www.odoo.com/documentation/19.0/
- **Odoo API Guide:** https://www.odoo.com/documentation/19.0/developer/reference/external_api.html
- **odoorpc Library:** https://github.com/OCA/odoorpc

---

**Last Updated:** 2026-01-19
**Version:** 1.0
