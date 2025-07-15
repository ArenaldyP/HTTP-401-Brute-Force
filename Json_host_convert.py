import re
import logging
import os

# Logging configuration
logging.basicConfig(
    filename="errors.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Configuration
INPUT_JSON = "IL_Code_401.json"
OUTPUT_HOSTS = "hosts.txt"

# Regex patterns
HOST_PATTERN = r'"host"\s*:\s*"([^"]+)"'
PORT_PATTERN = r'"port"\s*:\s*(\d+)'

def is_valid_ip_or_hostname(host):
    """Validasi apakah host adalah IP atau hostname yang valid."""
    # Validasi IP sederhana (IPv4)
    ip_pattern = r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    # Validasi hostname sederhana
    hostname_pattern = r"^[a-zA-Z0-9][a-zA-Z0-9-_\.]*[a-zA-Z0-9]$"
    return bool(re.match(ip_pattern, host) or re.match(hostname_pattern, host))

def convert_shodan_to_hosts(input_file=INPUT_JSON, output_file=OUTPUT_HOSTS):
    """
    Mengonversi file JSON Lines hasil Shodan menjadi format hosts.txt (host:port) menggunakan regex.
    """
    try:
        # Periksa apakah file ada dan tidak kosong
        if not os.path.exists(input_file):
            print(f"Error: {input_file} not found.")
            logging.error(f"Input file {input_file} not found.")
            return
        if os.path.getsize(input_file) == 0:
            print(f"Error: {input_file} is empty.")
            logging.error(f"Input file {input_file} is empty.")
            return

        # Ekstrak host dan port menggunakan regex
        hosts = []
        with open(input_file, "r", encoding="utf-8") as f:
            for line_number, line in enumerate(f, 1):
                try:
                    line = line.strip()
                    if not line:
                        logging.debug(f"Skipping empty line {line_number}")
                        continue

                    # Cari host dan port dengan regex
                    host_match = re.search(HOST_PATTERN, line)
                    port_match = re.search(PORT_PATTERN, line)

                    if not host_match or not port_match:
                        logging.warning(f"Missing host or port in line {line_number}: {line[:100]}...")
                        continue

                    ip = host_match.group(1)
                    port = int(port_match.group(1))

                    # Validasi data
                    if not is_valid_ip_or_hostname(ip):
                        logging.warning(f"Invalid host {ip} in line {line_number}")
                        continue
                    if not (1 <= port <= 65535):
                        logging.warning(f"Invalid port {port} for host {ip} in line {line_number}")
                        continue

                    hosts.append(f"{ip}:{port}")
                    logging.debug(f"Added host {ip}:{port} from line {line_number}")
                except Exception as e:
                    logging.error(f"Error processing line {line_number}: {e}")
                    continue

        if not hosts:
            print("No valid hosts found in the JSON file.")
            logging.info("No valid hosts found.")
            return

        # Tulis ke file hosts.txt
        with open(output_file, "w", encoding="utf-8") as f:
            for host in hosts:
                f.write(f"{host}\n")
        print(f"Successfully wrote {len(hosts)} hosts to {output_file}")
        logging.info(f"Successfully wrote {len(hosts)} hosts to {output_file}")

    except Exception as e:
        print(f"Error processing JSON file: {e}")
        logging.error(f"Error processing JSON file: {e}")

if __name__ == "__main__":
    print(f"Converting {INPUT_JSON} to {OUTPUT_HOSTS}...")
    convert_shodan_to_hosts()
    print("Conversion completed.")