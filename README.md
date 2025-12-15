# Deepfield Dashboard Export Tool

A Python utility to automatically backup and export Deepfield Defender dashboards to JSON files. Useful for dashboard version control, disaster recovery, and automation.

## Features

- ✅ **Automatic Custom Dashboard Export** - Export all custom (non-system) dashboards with a single command
- ✅ **Selective Export** - Export specific dashboards by slug
- ✅ **Dashboard Listing** - View all available dashboards with metadata
- ✅ **Full Configuration Backup** - Exports complete dashboard configuration including:
  - Permissions
  - Queries and query definitions
  - Sections and display layouts
  - Controls and filters
  - Description and labels
- ✅ **Flexible Backup Locations** - Specify custom backup directories
- ✅ **Comprehensive Logging** - Configurable log levels for debugging
- ✅ **Timestamp-based Filenames** - ISO 8601 format (`YYYY-MM-DDTHHMM SS-slug.json`)
- ✅ **Error Handling** - Detailed error reporting and recovery

## Requirements

- Python 3.6+
- `requests` library
- `deepy` library (Deepfield Python SDK) - for API key retrieval
- Access to Deepfield Defender instance with API enabled

## Installation

1. Clone or download the script:
   ```bash
   # Place export_dashboards.py in your working directory
   ```

2. Install required Python packages:
   ```bash
   pip install requests
   ```

3. Ensure the `deepy` library is available (installed with Deepfield Defender or SDK)

## Configuration

The script uses the Deepfield `deepy` library to automatically retrieve the API key. No manual configuration is required if you have:

- Deepfield Defender installed locally
- Proper authentication credentials configured
- Access to the API endpoint at `https://local.deepfield.net`

### Optional: Custom API Base URL

To use a different Deepfield instance, edit the `API_BASE_URL` variable in the script:

```python
API_BASE_URL = "https://your-deepfield-instance.com"
```

## Usage

### 1. Export All Custom Dashboards (Default)

Export all custom dashboards to the current directory:

```bash
python export_dashboards.py
```

Export to a specific backup directory:

```bash
python export_dashboards.py --backup-dir ./dashboards-backup
```

### 2. List All Available Dashboards

View all dashboards with their metadata:

```bash
python export_dashboards.py --list-dashboards
```

**Output:**
```
============================================================================
Found 15 dashboards:
============================================================================
ID    Name                                     Slug                            Labels                    System   Enabled
-----...-----...-----...-----...-----...-----...-----...-----...-----...-----...-----...-----...-----...-----...-----...-----
1     Firewall Filter Statistics               firewall-filter-statistics      Security/DDoS            Yes      Yes
13    DDoS Mitigation Dashboard                ddos-mitigation-dashboard       Security/DDoS            No       Yes
17    Custom Analytics Report                  custom-analytics-report         Analytics                No       Yes
```

### 3. Export Specific Dashboards by Slug

Export one or more specific dashboards:

```bash
python export_dashboards.py --dashboard firewall-filter-statistics ddos-mitigation-dashboard
```

Export to custom directory:

```bash
python export_dashboards.py --dashboard slug-1 slug-2 --backup-dir ./backups
```

### 4. Enable SSL Certificate Verification

By default, SSL verification is disabled for local instances. To enable it:

```bash
python export_dashboards.py --verify-ssl
```

### 5. Set Logging Level

Control verbosity of output:

```bash
# Debug level (most verbose)
python export_dashboards.py --log-level DEBUG

# Info level (default)
python export_dashboards.py --log-level INFO

# Warning level
python export_dashboards.py --log-level WARNING

# Error level (least verbose)
python export_dashboards.py --log-level ERROR
```

## Output Format

Exported dashboards are saved as JSON files with the following naming convention:

```
{TIMESTAMP}-{SLUG}.json
```

**Example:**
```
2025-12-15T143022-firewall-filter-statistics.json
2025-12-15T143045-ddos-mitigation-dashboard.json
```

### File Structure

Each exported JSON contains:

```json
{
  "enabled": true,
  "permissions": ["dfp.permission.name"],
  "queries": [...],
  "name": "Dashboard Name",
  "slug": "dashboard-slug",
  "sections": [...],
  "visible": true,
  "controls": [...],
  "description": "Dashboard description",
  "labels": ["Label1", "Label2"]
}
```

**Excluded Fields:**
The following metadata fields are excluded from exports (as they are system-generated):
- `id`, `created`, `modified`, `last_visited`, `favorite`, `is_homepage`, `is_default_home`, `system`

## Command Line Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--dashboard` | Multiple | None | Export specific dashboards by slug |
| `--list-dashboards` | Flag | False | List all available dashboards and exit |
| `--backup-dir` | Path | `.` (current) | Directory to save dashboard backups |
| `--verify-ssl` | Flag | False | Enable SSL certificate verification |
| `--log-level` | Choice | `INFO` | Logging level: DEBUG, INFO, WARNING, ERROR |

## Examples

### Scenario 1: Daily Backup of All Custom Dashboards

```bash
# Create backup directory
mkdir -p /backups/deepfield-dashboards

# Run backup
python export_dashboards.py --backup-dir /backups/deepfield-dashboards

# Schedule with cron (Linux/Mac):
# 0 2 * * * cd /path/to/script && python export_dashboards.py --backup-dir /backups/deepfield-dashboards
```

### Scenario 2: Backup Specific Dashboards to Version Control

```bash
# Export dashboards to git repository
python export_dashboards.py --dashboard firewall-filter-statistics ddos-mitigation-dashboard --backup-dir ./dashboards

# Commit changes
git add dashboards/
git commit -m "Dashboard backup: $(date +%Y-%m-%d)"
git push
```

### Scenario 3: Find and Export Dashboard by Name

```bash
# List all dashboards to find the slug
python export_dashboards.py --list-dashboards

# Export the desired dashboard
python export_dashboards.py --dashboard firewall-filter-statistics
```

### Scenario 4: Debug Export Issues

```bash
# Run with debug logging to see detailed API calls
python export_dashboards.py --log-level DEBUG --backup-dir ./debug-backup
```

## Logging

The script creates a log file `export_dashboards.log` in the current directory with detailed information about each export operation.

**Log Levels:**
- **DEBUG**: Detailed API calls, request/response data, full stack traces
- **INFO**: Progress updates, success/failure counts (default)
- **WARNING**: Warnings and non-critical issues
- **ERROR**: Errors only

## Troubleshooting

### Authentication Failed (401 Error)

**Issue:** Script cannot retrieve API key from `deepy` library

**Solutions:**
1. Ensure Deepfield is installed and running locally
2. Check that authentication credentials are configured
3. Verify API key with: `python -c "from deepy.deepui import get_default_root_api_key; print(get_default_root_api_key())"`

### Access Forbidden (403 Error)

**Issue:** Authenticated user lacks required permissions

**Solutions:**
1. Verify user has dashboard view/access permissions
2. Contact Deepfield administrator to grant permissions
3. Check `export_dashboards.log` for specific permission requirements

### Dashboard Not Found (404 Error)

**Issue:** Specified dashboard slug doesn't exist

**Solutions:**
1. List all dashboards: `python export_dashboards.py --list-dashboards`
2. Verify correct slug spelling
3. Check that dashboard hasn't been deleted

### Missing Fields in Export

**Issue:** Exported JSON is missing `permissions`, `queries`, `sections`, or `controls`

**Solutions:**
1. This typically means the dashboard fetch failed silently
2. Check logs: `tail export_dashboards.log`
3. Try with `--log-level DEBUG` for more details
4. Ensure dashboard is accessible via the API endpoint

### Directory Creation Failed

**Issue:** Cannot create backup directory

**Solutions:**
1. Check parent directory permissions
2. Use absolute path instead of relative: `--backup-dir /full/path/to/backup`
3. Ensure sufficient disk space
4. Run with appropriate privileges (sudo if needed on Linux/Mac)

## Performance Considerations

- **List operation:** O(1) - Single API call
- **Default export (all custom dashboards):** O(n) where n = number of custom dashboards
  - Makes 2 API calls: one to list, then one per dashboard for full details
- **Selective export (--dashboard):** O(m) where m = number of specified dashboards
  - Makes 1 API call per dashboard

For instances with many dashboards, expect proportionally longer execution times.

## Integration with Scheduling Tools

### Linux/Mac - Cron

```bash
# Add to crontab (crontab -e)
# Daily backup at 2 AM
0 2 * * * cd /path/to/script && /usr/bin/python3 export_dashboards.py --backup-dir /backups/dashboards >> /var/log/deepfield-backup.log 2>&1
```

### Windows - Task Scheduler

```powershell
# Create scheduled task
$trigger = New-ScheduledTaskTrigger -Daily -At 2am
$action = New-ScheduledTaskAction -Execute "C:\Python39\python.exe" -Argument "C:\path\to\export_dashboards.py --backup-dir C:\Backups\Dashboards"
Register-ScheduledTask -TaskName "Deepfield-Dashboard-Backup" -Trigger $trigger -Action $action -RunLevel Highest
```

## Support and Issues

For issues or questions:

1. Check the log file: `export_dashboards.log`
2. Run with `--log-level DEBUG` to see detailed information
3. Verify API connectivity: `curl https://local.deepfield.net/api/dashboards`
4. Contact your Deepfield administrator for API/permission issues

## License

This script is provided as-is for use with Deepfield Defender.

## Version History

- **v1.0** (2025-12-15): Initial release
  - Dashboard listing
  - Full dashboard export (custom dashboards)
  - Selective dashboard export by slug
  - Configurable backup directories
  - Comprehensive logging
