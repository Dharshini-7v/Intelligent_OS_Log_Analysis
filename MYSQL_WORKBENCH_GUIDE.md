# 🔧 MySQL Workbench Connection Guide

## Quick Connection Steps

### Step 1: Open MySQL Workbench

### Step 2: Create New Connection
1. Click the **"+"** icon next to "MySQL Connections"
2. Or go to **Database → New Connection**

### Step 3: Enter Connection Details

Fill in these fields:

| Field | Value |
|-------|-------|
| **Connection Name** | `Intelligent Log Analysis` (or any name) |
| **Connection Method** | Standard (TCP/IP) |
| **Hostname** | `localhost` |
| **Port** | `3306` |
| **Username** | `log_analyzer` |
| **Password** | `LogAnalyzer@2026` |
| **Default Schema** | `intelligent_log_analysis` |

### Step 4: Test Connection
- Click **"Test Connection"**
- Should see: ✅ **"Successfully made the MySQL connection"**

### Step 5: Save
- Click **"OK"**

### Step 6: View Database
- Double-click the connection to open it
- In the left panel under **Schemas**, expand `intelligent_log_analysis`
- You'll see all 6 tables:
  - `users`
  - `log_templates`
  - `patterns`
  - `anomalies`
  - `predictions`
  - `system_metrics`

---

## View Table Data

1. Right-click any table → **"Select Rows - Limit 1000"**
2. Or double-click the table name to open the table viewer
3. You'll see all columns and data in a grid view

---

## Example Queries to Run

Click **File → New Query Tab** and paste:

```sql
-- Show all tables
SHOW TABLES;

-- Show users table structure
DESCRIBE users;

-- Show all users
SELECT * FROM users;

-- Show patterns
SELECT * FROM patterns;

-- Count records in each table
SELECT 
  'users' as table_name, COUNT(*) as row_count FROM users
UNION ALL
SELECT 'log_templates', COUNT(*) FROM log_templates
UNION ALL
SELECT 'patterns', COUNT(*) FROM patterns
UNION ALL
SELECT 'anomalies', COUNT(*) FROM anomalies
UNION ALL
SELECT 'predictions', COUNT(*) FROM predictions
UNION ALL
SELECT 'system_metrics', COUNT(*) FROM system_metrics;
```

---

## Connection Details (For Reference)

```
Host:     localhost
Port:     3306
User:     log_analyzer
Password: LogAnalyzer@2026
Database: intelligent_log_analysis
```

---

## 💡 Tips for Your Staff Presentation

1. **Show the Schema**: Expand `intelligent_log_analysis` in left panel
2. **Show Table Structure**: Right-click table → "Inspect Table"
3. **Show Sample Data**: Double-click table to see grid view
4. **Show Database Statistics**: Run the "count query" above
5. **Take Screenshots**: Use Workbench's built-in export features

You're all set! Your database is ready for tomorrow's submission. 🎉
