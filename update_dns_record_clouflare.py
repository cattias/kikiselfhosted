import requests
import os
import json
import time

# --- Configuration ---
# Cloudflare API Base URL
CLOUDFLARE_API_BASE = "https://api.cloudflare.com/client/v4"

# REQUIRED: Your domain (e.g., 'example.com')
DOMAIN = os.getenv('CLOUDFLARE_DOMAIN') 
# REQUIRED: The record name, typically '@' for the root domain A record, or 'home' for a subdomain
RECORD_NAME = os.getenv('CLOUDFLARE_RECORD_NAME', '@') 
# REQUIRED: Set this to 'live' for production updates, or 'test' for development.
ENVIRONMENT = os.getenv('CLOUDFLARE_ENVIRONMENT', 'live')

# Authentication Headers (Uses a Bearer Token)
HEADERS = {
    'Content-Type': 'application/json',
    # We use CLOUDFLARE_API_TOKEN, which should have Zone:DNS:Edit permissions
    'Authorization': f'Bearer {os.getenv("CLOUDFLARE_API_TOKEN")}'
}

# --- Utility Functions ---

def get_public_ip():
    """Fetches the current external public IP address."""
    print("-> 1. Fetching current public IP address...")
    try:
        # Using a reliable, simple service to get the external IP
        response = requests.get('https://api.ipify.org', timeout=5)
        response.raise_for_status()
        current_ip = response.text.strip()
        print(f"   Success. Current public IP is: {current_ip}")
        return current_ip
    except requests.RequestException as e:
        print(f"   Error fetching public IP: {e}")
        return None

def get_zone_id():
    """Retrieves the Zone ID for the given domain from Cloudflare."""
    url = f"{CLOUDFLARE_API_BASE}/zones?name={DOMAIN}"
    print(f"-> 2. Fetching Zone ID for {DOMAIN}...")

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get('success') and data['result']:
            zone_id = data['result'][0]['id']
            print(f"   Success. Zone ID found: {zone_id}")
            return zone_id
        else:
            print(f"   Error: Could not find Zone ID for {DOMAIN}. Check domain spelling and API permissions.")
            print(f"   API Response: {data}")
            return None
    except requests.RequestException as e:
        print(f"   Connection Error fetching Zone ID: {e}")
        return None

def get_current_a_record(zone_id):
    """Retrieves the current A record IP and the Record ID from Cloudflare."""
    
    # Cloudflare API requires the full record name (e.g., 'example.com' or 'home.example.com')
    full_record_name = f"{RECORD_NAME}.{DOMAIN}" if RECORD_NAME != '@' else DOMAIN
    
    url = f"{CLOUDFLARE_API_BASE}/zones/{zone_id}/dns_records?type=A&name={full_record_name}"
    print(f"-> 3. Checking current A record for {full_record_name}...")

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get('success') and data['result']:
            record = data['result'][0]
            cloudflare_ip = record['content']
            record_id = record['id']
            print(f"   Success. Cloudflare A record IP is: {cloudflare_ip} (Record ID: {record_id})")
            return cloudflare_ip, record_id
        else:
            print(f"   Warning: A record for {full_record_name} not found. Ensure the record exists.")
            return None, None

    except requests.RequestException as e:
        print(f"   Connection Error checking record: {e}")
        return None, None

def update_a_record(zone_id, record_id, old_ip, new_ip):
    """Updates the A record on Cloudflare with the new IP address."""
    full_record_name = f"{RECORD_NAME}.{DOMAIN}" if RECORD_NAME != '@' else DOMAIN
    url = f"{CLOUDFLARE_API_BASE}/zones/{zone_id}/dns_records/{record_id}"
    
    # TTL is set to 60 seconds (minimum)
    payload = {
        'type': 'A',
        'name': full_record_name,
        'content': new_ip,
        'ttl': 60, 
        'proxied': False # DDNS records are usually not proxied
    }

    print(f"-> 4. Attempting to update A record from {old_ip} to: {new_ip}")
    
    if ENVIRONMENT.lower() != 'live':
        print("   --- TEST MODE: Update skipped. Set CLOUDFLARE_ENVIRONMENT='live' to enable updates. ---")
        return True # Simulate success in test mode

    try:
        # Cloudflare update API uses PUT
        response = requests.put(url, headers=HEADERS, data=json.dumps(payload), timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('success'):
            print(f"   SUCCESS: A record for {full_record_name} updated to {new_ip}!")
            return True
        else:
            print(f"   FAILED to update record. Errors: {data.get('errors')}")
            return False

    except requests.RequestException as e:
        print(f"   Connection Error during update: {e}")
        return False

# --- Main Logic ---

def main():
    """The main function to execute the DDNS check and update."""
    print("--- Cloudflare DDNS Updater Script Starting ---")
    
    required_env_vars = ["CLOUDFLARE_API_TOKEN", "CLOUDFLARE_DOMAIN"]
    for var in required_env_vars:
        if not os.getenv(var):
            print(f"\nFATAL ERROR: Environment variable '{var}' is missing.")
            print("Please set the required environment variables. See README_CLOUDFLARE.md for details.")
            return
    
    public_ip = get_public_ip()
    if not public_ip:
        print("\nScript aborted: Could not determine public IP.")
        return

    zone_id = get_zone_id()
    if not zone_id:
        print("\nScript aborted: Could not determine Cloudflare Zone ID.")
        return

    cloudflare_ip, record_id = get_current_a_record(zone_id)
    if not cloudflare_ip or not record_id:
        print("\nScript aborted: Could not retrieve current Cloudflare IP or Record ID.")
        return

    if public_ip == cloudflare_ip:
        print("\n-> 5. IPs match. No update required.")
    else:
        print(f"\n-> 5. IPs MISMATCH: Public IP ({public_ip}) vs Cloudflare IP ({cloudflare_ip})")
        update_a_record(zone_id, record_id, cloudflare_ip, public_ip)

if __name__ == "__main__":
    main()

