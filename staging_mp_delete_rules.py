import csv
import json
import sys
import requests
import dns.resolver
import threading
import queue

# Check if the script was called with a filename argument; exit if not.
if len(sys.argv) < 2:
    print('No file provided, no rules to upload')
    sys.exit()
else:
    file_name = sys.argv[1]  # Assign the filename provided as argument to file_name.

tasks_queue = queue.Queue()  # Initialize a queue for tasks.

# Function to get the canonical name for a given hostname using DNS resolution.
def _get_canonical_name(hostname_www):
    print('Attempting to get canonical name for %s' % hostname_www)
    resolver = dns.resolver.Resolver()  # Create a new DNS resolver instance.
    try:
        # Attempt to resolve the hostname to its canonical name.
        canonical_name = resolver.resolve(hostname_www).canonical_name.to_unicode().rstrip('.')
    except dns.resolver.NXDOMAIN:
        # If the domain does not exist, print a message and return None.
        print('Nonexistent domain %s' % hostname_www)
        return None
    if canonical_name != hostname_www:
        # If a canonical name was found, print it.
        print('%s has canonical name %s' % (hostname_www, canonical_name))
    return canonical_name

# Get the canonical name for 'www.playstation.com' and replace part of it for staging purposes.
get_canonical_name = _get_canonical_name('www.playstation.com')

if get_canonical_name:
    staging_host = get_canonical_name.replace('akamaiedge', 'akamaiedge-staging')
else:
    sys.exit('Failed to get canonical name')  # Exit if canonical name could not be obtained.

# Function to resolve the A record for the staging host.
def resolveDNSA():
    domain = staging_host
    resolver = dns.resolver.Resolver()
    answer = resolver.resolve(domain, "A")
    return answer

resultDNSA = resolveDNSA()  # Perform the DNS A record resolution.
resultant_str = ''.join(str(item) for item in resultDNSA)  # Convert DNS answer to a string.

#print(resultant_str)  # Print the result of the DNS A record resolution.

# Custom adapter for requests library to allow setting the Host header explicitly.
class HostHeaderSSLAdapter(requests.adapters.HTTPAdapter):
    def resolve(self, hostname):
        ips = resultant_str  # Use the previously obtained DNS resolution result.
        resolutions = {'paulm-sony.test.edgekey.net': ips}
        return resolutions.get(hostname)

    def send(self, request, **kwargs):
        from urllib.parse import urlparse

        connection_pool_kwargs = self.poolmanager.connection_pool_kw
        result = urlparse(request.url)
        resolved_ip = self.resolve(result.hostname)

        if result.scheme == 'https' and resolved_ip:
            # Modify the request URL to use the resolved IP address, and set necessary headers.
            request.url = request.url.replace(
                'https://' + result.hostname,
                'https://' + resolved_ip,
            )
            connection_pool_kwargs['server_hostname'] = result.hostname
            connection_pool_kwargs['assert_hostname'] = result.hostname

            request.headers['Host'] = result.hostname
        else:
            # Remove server_hostname and assert_hostname from the connection pool kwargs if not HTTPS.
            connection_pool_kwargs.pop('server_hostname', None)
            connection_pool_kwargs.pop('assert_hostname', None)

        return super(HostHeaderSSLAdapter, self).send(request, **kwargs)

# Worker function for threads, processes rows from the task queue.
def thread_worker():
    while True:
        row = tasks_queue.get()
        if row is None:  # If a None task is received, terminate the loop.
            break
        process_row(row)  # Process the row.
        tasks_queue.task_done()  # Indicate that a formerly enqueued task is complete.

# Function to process each row from the CSV file; makes a POST request with the row data.
def process_row(row):
    json_data = json.dumps(row)  # Convert row to JSON.
    print(json_data)  # Print the JSON data.
    url = 'https://paulm-sony.test.edgekey.net/staging/upload'  # Define the URL for the POST request.
    headers = {"Content-type": "application/json", "User-Agent": "paul-python"}  # Set custom headers.
    requests.packages.urllib3.disable_warnings()  # Disable warnings about SSL certificate verification.
    session = requests.Session()  # Create a new session.
    session.mount('https://', HostHeaderSSLAdapter())  # Mount the custom adapter for HTTPS requests.
    response = session.post(url, data=json_data, headers=headers, verify=False)  # Make the POST request.
    print(response.status_code, response.reason)  # Print the response status code and reason.

# Start a pool of threads to process the tasks.
num_threads = 4
threads = []
for i in range(num_threads):
    t = threading.Thread(target=thread_worker)
    threads.append(t)
    t.start()

# Open the CSV file and enqueue each row as a task for processing.
with open(file_name, newline='') as csvfile:
    csvreader = csv.reader(csvfile)
    for row in csvreader:
        tasks_queue.put(row)  # Enqueue the row for processing.

# Block until all tasks in the queue have been processed.
tasks_queue.join()

# Stop the worker threads.
for i in range(num_threads):
    tasks_queue.put(None)  # Send None to signal threads to terminate.
for t in threads:
    t.join()  # Wait for all threads to terminate.
