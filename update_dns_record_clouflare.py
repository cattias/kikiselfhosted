import requests
import json
import time
import argparse # NEW: Import for command-line argument parsing

# --- Configuration ---
# Cloudflare API Base URL
CLOUDFLARE_API_BASE = "https://api.cloudflare.com/client/v4"

# HEADERS template (Token will be injected in main)
HEADERS_TEMPLATE = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer {}' 
}

# --- Argument Parsing ---

def parse_arguments():
    """Parses command-line arguments for configuration."""
    parser = argparse.ArgumentParser(
        description="Cloudflare Dynamic DNS (DDNS) Updater for A records. Uses command-line parameters instead of environment variables.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        '--token', 
        required=True, 
        help="The Cloudflare API Token with Zone:DNS:Edit permissions."
    )
    parser.add_argument(
        '--domain', 
        required=True, 
        help="Your registered domain (e.g., 'example.com')."
    )
    parser.add_argument(
        '--name', 
        default='@', 
        help="The DNS record name (e.g., '@' for root, or 'home' for subdomain 'home.example.com'). Defaults to '@'."
    )
    parser.add_argument(
        '--env', 
        default='live', 
        choices=['live', 'test'], 
        help="The execution environment/mode. 'live' performs updates, 'test' simulates them. Defaults to 'live'."
    )
    return parser.parse_args()


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

def get_zone_id(domain, headers):
    """Retrieves the Zone ID for the given domain from Cloudflare."""
    url = f"{CLOUDFLARE_API_BASE}/zones?name={domain}"
    print(f"-> 2. Fetching Zone ID for {domain}...")

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get('success') and data['result']:
            zone_id = data['result'][0]['id']
            print(f"   Success. Zone ID found: {zone_id}")
            return zone_id
        else:
            print(f"   Error: Could not find Zone ID for {domain}. Check domain spelling and API permissions.")
            print(f"   API Response: {data}")
            return None
    except requests.RequestException as e:
        print(f"   Connection Error fetching Zone ID: {e}")
        return None

def get_current_a_record(zone_id, domain, record_name, headers):
    """Retrieves the current A record IP and the Record ID from Cloudflare."""
    
    # Cloudflare API requires the full record name (e.g., 'example.com' or 'home.example.com')
    full_record_name = f"{record_name}.{domain}" if record_name != '@' else domain
    
    url = f"{CLOUDFLARE_API_BASE}/zones/{zone_id}/dns_records?type=A&name={full_record_name}"
    print(f"-> 3. Checking current A record for {full_record_name}...")

    try:
        response = requests.get(url, headers=headers, timeout=10)
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

def update_a_record(zone_id, record_id, old_ip, new_ip, domain, record_name, environment, headers):
    """Updates the A record on Cloudflare with the new IP address."""
    full_record_name = f"{record_name}.{domain}" if record_name != '@' else domain
    url = f"{CLOUDFLARE_API_BASE}/zones/{zone_id}/dns_records/{record_id}"
    
    # TTL is set to 60 seconds (minimum)
    payload = {
        'type': 'A',
        'name': full_record_name,
        'content': new_ip,
        'ttl': 60, 
        'proxied': True
    }

    print(f"-> 4. Attempting to update A record from {old_ip} to: {new_ip}")
    
    if environment.lower() != 'live':
        print("   --- TEST MODE: Update skipped. Use '--env live' to enable updates. ---")
        return True # Simulate success in test mode

    try:
        # Cloudflare update API uses PUT
        response = requests.put(url, headers=headers, data=json.dumps(payload), timeout=10)
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
    
    # NEW: Parse command-line arguments
    args = parse_arguments()
    
    token = args.token
    domain = args.domain
    record_name = args.name
    environment = args.env
    
    # NEW: Prepare the full headers object with the token
    headers = HEADERS_TEMPLATE.copy()
    headers['Authorization'] = headers['Authorization'].format(token)

    print("--- Cloudflare DDNS Updater Script Starting ---")
    
    public_ip = get_public_ip()
    if not public_ip:
        print("\nScript aborted: Could not determine public IP.")
        return

    # Pass the arguments to the utility functions
    zone_id = get_zone_id(domain, headers)
    if not zone_id:
        print("\nScript aborted: Could not determine Cloudflare Zone ID.")
        return

    cloudflare_ip, record_id = get_current_a_record(zone_id, domain, record_name, headers)
    if not cloudflare_ip or not record_id:
        print("\nScript aborted: Could not retrieve current Cloudflare IP or Record ID.")
        return

    if public_ip == cloudflare_ip:
        print("\n-> 5. IPs match. No update required.")
    else:
        print(f"\n-> 5. IPs MISMATCH: Public IP ({public_ip}) vs Cloudflare IP ({cloudflare_ip})")
        # Pass all necessary arguments to the update function
        update_a_record(zone_id, record_id, cloudflare_ip, public_ip, domain, record_name, environment, headers)

if __name__ == "__main__":
    main()

