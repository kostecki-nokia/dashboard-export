import argparse
import csv
import requests
import sys
import json
import logging
import os
from typing import List, Dict, Optional
from datetime import datetime
from time import time

# Configure basic logger - will be reconfigured in main() with user-specified level
logger = logging.getLogger(__name__)

# Suppress NumExpr informational messages
logging.getLogger('numexpr').setLevel(logging.WARNING)

# Silence warnings about unverified SSL certificates
try:
    requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
except AttributeError:
    logger.warning("Could not disable SSL warnings.")

# Import the 'deepy' library
try:
    from deepy.deepui import get_default_root_api_key
except ImportError:
    logger.error("Could not import 'get_default_root_api_key'.")
    logger.error("Please ensure the 'deepy' library is installed and available in your PYTHONPATH.")
    sys.exit(1)

# --- CONFIGURATION ---
API_BASE_URL = "https://local.deepfield.net"

try:
    API_KEY = get_default_root_api_key()
    if not API_KEY:
        logger.error("get_default_root_api_key() returned an empty key.")
        sys.exit(1)
    logger.info("Successfully retrieved API key from deepy.")
except Exception as e:
    logger.error(f"Failed to retrieve API key from deepy: {e}")
    sys.exit(1)

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

PARAMS = {
    "api_key": API_KEY
}


def fetch_dashboards(verify_ssl: bool = False, dashboard_names: Optional[List[str]] = None) -> Optional[List[Dict]]:
    """
    Fetches dashboards from the API, optionally filtered by name.
    
    Args:
        verify_ssl: Whether to verify SSL certificates
        dashboard_names: Optional list of dashboard names to filter by
        
    Returns:
        List of dashboard dictionaries or None on failure
    """
    logger.info("Fetching dashboards from API...")
    url = f"{API_BASE_URL}/api/dashboards"

    try:
        response = requests.get(url, headers=HEADERS, params=PARAMS, verify=verify_ssl)
        
        if response.status_code == 401:
            logger.error("Authentication failed. Check your API key.")
            return None
        elif response.status_code == 403:
            logger.error("Access forbidden. Check your permissions.")
            return None
        
        response.raise_for_status()
        data = response.json()
        
        # Dashboards API returns a list directly
        if not isinstance(data, list):
            logger.error(f"Expected list of dashboards, got {type(data)}")
            return None
        
        dashboards = data
        logger.info(f"Fetched {len(dashboards)} dashboards from API")
        
        # Filter by dashboard names if specified
        if dashboard_names:
            original_count = len(dashboards)
            dashboards = [d for d in dashboards if d.get('name') in dashboard_names]
            logger.info(f"Filtered from {original_count} to {len(dashboards)} matching dashboards.")
        
        if not dashboards:
            logger.warning("No dashboards found or matched filters.")
        else:
            logger.info(f"Successfully fetched {len(dashboards)} dashboards.")
        
        return dashboards
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch dashboards: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse API response: {e}")
        return None


def fetch_dashboard_by_slug(slug: str, verify_ssl: bool = False) -> Optional[Dict]:
    """
    Fetches a specific dashboard by slug from the API.
    
    Args:
        slug: Dashboard slug identifier
        verify_ssl: Whether to verify SSL certificates
        
    Returns:
        Dashboard dictionary or None on failure
    """
    logger.info(f"Fetching dashboard with slug '{slug}'...")
    url = f"{API_BASE_URL}/api/dashboards/{slug}"

    try:
        response = requests.get(url, headers=HEADERS, params=PARAMS, verify=verify_ssl)
        
        if response.status_code == 401:
            logger.error("Authentication failed. Check your API key.")
            return None
        elif response.status_code == 403:
            logger.error("Access forbidden. Check your permissions.")
            return None
        elif response.status_code == 404:
            logger.error(f"Dashboard with slug '{slug}' not found (404).")
            return None
        
        response.raise_for_status()
        dashboard = response.json()
        
        logger.info(f"Successfully fetched dashboard '{slug}'")
        return dashboard
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch dashboard '{slug}': {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse API response for '{slug}': {e}")
        return None


def export_dashboard_to_json(dashboard: Dict, output_dir: str = ".") -> bool:
    """
    Exports a dashboard to a JSON file with timestamp prefix.
    
    Args:
        dashboard: Dashboard dictionary
        output_dir: Directory to save the file in (default: current directory)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        slug = dashboard.get('slug', 'unknown')
        timestamp_str = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        filename = f"{timestamp_str}-{slug}.json"
        filepath = os.path.join(output_dir, filename)
        
        logger.info(f"Exporting dashboard '{slug}' to {filepath}...")
        
        # Define the fields to exclude from export
        exclude_fields = {
            'id', 'created', 'modified', 'last_visited', 'favorite', 
            'is_homepage', 'is_default_home', 'system'
        }
        
        # Build the export dictionary with all fields except excluded ones
        export_data = {k: v for k, v in dashboard.items() if k not in exclude_fields}
        
        # Define the preferred field order for the output
        field_order = [
            'enabled', 'permissions', 'queries', 'name', 'slug', 'sections', 
            'visible', 'controls', 'description', 'labels'
        ]
        
        # Reorder the export data based on preferred order, then add remaining fields
        ordered_data = {}
        for field in field_order:
            if field in export_data:
                ordered_data[field] = export_data.pop(field)
        
        # Add any remaining fields that weren't in the preferred order
        ordered_data.update(export_data)
        export_data = ordered_data
        
        # Write to JSON file with pretty formatting
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✓ Successfully exported dashboard '{slug}' to {filepath}")
        return True
        
    except IOError as e:
        logger.error(f"Failed to write JSON file: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during export: {e}")
        logger.exception(e)
        return False


def format_timestamp(timestamp: int) -> str:
    """
    Converts Unix timestamp to human-readable format.
    
    Args:
        timestamp: Unix timestamp
        
    Returns:
        Formatted date string
    """
    try:
        if timestamp:
            return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, OSError):
        pass
    return "N/A"


def main():
    parser = argparse.ArgumentParser(
        description="Fetches dashboards from Deepfield Defender and exports to JSON.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export all custom dashboards to current directory
  python export_dashboards.py
  
  # Export all custom dashboards to specific backup directory
  python export_dashboards.py --backup-dir ./dashboards-backup
  
  # List all available dashboards
  python export_dashboards.py --list-dashboards
  
  # Export specific dashboards by slug
  python export_dashboards.py --dashboard firewall-filter-statistics traffic-by-site-power-users
  
  # Export specific dashboards to custom backup directory
  python export_dashboards.py --dashboard slug-1 slug-2 --backup-dir ./backups
        """
    )

    parser.add_argument(
        "--dashboard",
        nargs='+',
        help="Export specific dashboards by slug (e.g., dashboard-slug-1 dashboard-slug-2). Saves as JSON files."
    )
    parser.add_argument(
        "--verify-ssl", 
        action="store_true",
        help="Verify SSL certificates (default: False for local.deepfield.net)"
    )
    parser.add_argument(
        "--log-level",
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help="Set logging level (default: INFO)"
    )
    parser.add_argument(
        "--list-dashboards",
        action="store_true",
        help="List all available dashboards and exit"
    )
    parser.add_argument(
        "--backup-dir",
        default=".",
        help="Directory to save dashboard backups (default: current directory)"
    )

    args = parser.parse_args()
    
    # Configure logging with user-specified level
    log_level = getattr(logging, args.log_level)
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('export_dashboards.log', mode='w')
        ],
        force=True  # Force reconfiguration
    )
    logger.setLevel(log_level)
    
    # Ensure handlers also respect the log level
    for handler in logging.root.handlers:
        handler.setLevel(log_level)
    
    if args.verify_ssl:
        logger.info("SSL certificate verification is ENABLED")
    else:
        logger.warning("SSL certificate verification is DISABLED")
    
    # Ensure backup directory exists
    backup_dir = args.backup_dir
    if not os.path.exists(backup_dir):
        try:
            os.makedirs(backup_dir, exist_ok=True)
            logger.info(f"Created backup directory: {backup_dir}")
        except OSError as e:
            logger.error(f"Failed to create backup directory '{backup_dir}': {e}")
            sys.exit(1)

    try:
        # Handle --dashboard (slug export) option
        if args.dashboard:
            logger.info(f"{'='*60}")
            logger.info(f"Exporting {len(args.dashboard)} dashboard(s) by slug...")
            logger.info(f"Slugs: {', '.join(args.dashboard)}")
            logger.info(f"Backup directory: {backup_dir}")
            logger.info(f"{'='*60}")
            
            success_count = 0
            failure_count = 0
            
            for slug in args.dashboard:
                dashboard = fetch_dashboard_by_slug(slug, verify_ssl=args.verify_ssl)
                
                if dashboard is None:
                    logger.error(f"Failed to fetch dashboard '{slug}'.")
                    failure_count += 1
                    continue
                
                if export_dashboard_to_json(dashboard, backup_dir):
                    success_count += 1
                else:
                    failure_count += 1
            
            logger.info(f"{'='*60}")
            logger.info(f"Dashboard export completed: {success_count} successful, {failure_count} failed")
            logger.info(f"{'='*60}")
            
            if failure_count > 0:
                sys.exit(1)
            sys.exit(0)
        
        # Handle --list-dashboards option
        if args.list_dashboards:
            logger.info("Fetching all dashboards...")
            dashboards = fetch_dashboards(verify_ssl=args.verify_ssl, dashboard_names=None)
            
            if dashboards is None:
                logger.error("Failed to fetch dashboards.")
                sys.exit(1)
            
            if not dashboards:
                logger.warning("No dashboards found.")
                sys.exit(0)
            
            print("\n" + "="*130)
            print(f"Found {len(dashboards)} dashboards:")
            print("="*130)
            print(f"{'ID':<5} {'Name':<40} {'Slug':<35} {'Labels':<25} {'System':<8} {'Enabled':<8}")
            print("-"*130)
            
            for dash in sorted(dashboards, key=lambda x: x.get('name', '')):
                dash_id = dash.get('id', 'N/A')
                dash_name = dash.get('name', 'N/A')[:40]
                dash_slug = dash.get('slug', 'N/A')[:35]
                labels = ', '.join(dash.get('labels', []))[:25]
                system = 'Yes' if dash.get('system') else 'No'
                enabled = 'Yes' if dash.get('enabled') else 'No'
                
                print(f"{dash_id:<5} {dash_name:<40} {dash_slug:<35} {labels:<25} {system:<8} {enabled:<8}")
            
            print("="*130)
            print(f"\nTo export dashboards by slug, use:")
            print(f'  python export_dashboards.py --dashboard slug-1 slug-2 slug-3')
            sys.exit(0)
        
        # If no action specified, export all custom (non-system) dashboards
        logger.info(f"{'='*60}")
        logger.info("No action specified. Exporting all custom dashboards (system=false)...")
        logger.info(f"Backup directory: {backup_dir}")
        logger.info(f"{'='*60}")
        
        # Fetch all dashboards
        dashboards = fetch_dashboards(verify_ssl=args.verify_ssl, dashboard_names=None)
        
        if dashboards is None:
            logger.error("Failed to fetch dashboards. Exiting.")
            sys.exit(1)
        
        # Filter to only custom dashboards (system=false)
        custom_dashboards = [d for d in dashboards if not d.get('system', False)]
        
        if not custom_dashboards:
            logger.warning("No custom dashboards found to export.")
            sys.exit(0)
        
        logger.info(f"Found {len(custom_dashboards)} custom dashboard(s) to export")
        
        success_count = 0
        failure_count = 0
        
        for dashboard in custom_dashboards:
            # Fetch full dashboard details for each dashboard
            slug = dashboard.get('slug')
            if not slug:
                logger.error("Dashboard missing slug, skipping.")
                failure_count += 1
                continue
            
            full_dashboard = fetch_dashboard_by_slug(slug, verify_ssl=args.verify_ssl)
            if full_dashboard is None:
                logger.error(f"Failed to fetch full details for dashboard '{slug}'.")
                failure_count += 1
                continue
            
            if export_dashboard_to_json(full_dashboard, backup_dir):
                success_count += 1
            else:
                failure_count += 1
        
        logger.info(f"{'='*60}")
        logger.info(f"Dashboard export completed: {success_count} successful, {failure_count} failed")
        logger.info(f"{'='*60}")
        
        if failure_count > 0:
            sys.exit(1)
        
    except KeyboardInterrupt:
        logger.warning("\nScript interrupted by user.")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.exception(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
