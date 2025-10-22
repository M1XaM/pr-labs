import threading
import http.client
import time

HOST = "127.0.0.1"
PORT = 8080
PATH = "/index.html"
N = 50  # number of concurrent requests

results = [None] * N

def request_worker(i):
    try:
        conn = http.client.HTTPConnection(HOST, PORT, timeout=5)
        conn.request("GET", PATH)
        resp = conn.getresponse()
        resp.read()
        conn.close()
        results[i] = resp.status
    except:
        results[i] = None

threads = []
start = time.time()
for i in range(N):
    t = threading.Thread(target=request_worker, args=(i,))
    t.start()
    threads.append(t)

for t in threads:
    t.join()
end = time.time()

ok = sum(1 for r in results if r == 200)
print(f"Requests sent: {N}, successful: {ok}, time: {end-start:.2f}s")
