import threading
import time

NUM_THREADS = 10
INCREMENTS_PER_THREAD = 100000
EXPECTED_TOTAL = NUM_THREADS * INCREMENTS_PER_THREAD

# Shared resources
global_counter = 0
counter_lock = threading.Lock() 

def naive_worker_forced_failure():
    global global_counter
    for _ in range(INCREMENTS_PER_THREAD):
        current_value = global_counter 
        time.sleep(0.000001) 
        global_counter = current_value + 1

def synchronized_worker():
    global global_counter
    for _ in range(INCREMENTS_PER_THREAD):
        with counter_lock:
            global_counter += 1

def run_test(worker_func, title):
    global global_counter
    global_counter = 0
    
    print(f"\nRunning: {title}")
    
    threads = []
    start_time = time.perf_counter()
    
    for i in range(NUM_THREADS):
        thread = threading.Thread(target=worker_func)
        threads.append(thread)
        thread.start()
        
    for thread in threads:
        thread.join()
        
    end_time = time.perf_counter()
    
    print(f"Threads: {NUM_THREADS}")
    print(f"Increments per thread: {INCREMENTS_PER_THREAD:,}")
    print(f"Expected final count: {EXPECTED_TOTAL:,}")
    print(f"Actual final count: {global_counter:,}")
    print(f"Execution time: {end_time - start_time:.4f} seconds")
    
    if global_counter == EXPECTED_TOTAL:
        print("RESULT: Success (Thread-safe)")
    else:
        print("RESULT: Failure (Race condition detected! Lost updates: {:,})".format(EXPECTED_TOTAL - global_counter))

if __name__ == "__main__":    
    run_test(naive_worker_forced_failure, "NAIVE TEST")
    run_test(synchronized_worker, "SYNCHRONIZED TEST (THREAD-SAFE)")
