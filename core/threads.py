import time
import requests
from queue import Empty

def stat_updater(count_queue):
    """Bijhouden van statistieken."""
    total_scanned = 0
    start_time = time.time()
    
    while True:
        try:
            # Haal data uit de queue zonder te blokkeren
            try:
                chunks = count_queue.get(timeout=1)
                for ts, count in chunks:
                    total_scanned += count
            except Empty:
                pass
            
            elapsed = time.time() - start_time
            if elapsed >= 10:
                speed = total_scanned / elapsed if elapsed > 0 else 0
                print(f"[ STATS ] Snelheid: {speed:.2f} groepen/sec")
                start_time = time.time()
        except Exception as e:
            print(f"[ STATS ERROR ] {e}")
        time.sleep(1)

def log_notifier(log_queue, webhook_url):
    """Stuurt hits naar Discord/Guilded."""
    while True:
        try:
            group_info = log_queue.get(timeout=1)
            print(f"[ HIT! ] Groep gevonden: {group_info}")
            
            if webhook_url:
                payload = {
                    "content": f"🎉 **Groep Zonder Eigenaar Gevonden!**\nhttps://www.roblox.com/groups/{group_info}"
                }
                requests.post(webhook_url, json=payload, timeout=5)
        except Empty:
            pass
        except Exception as e:
            print(f"[ WEBHOOK ERROR ] {e}")
        time.sleep(0.5)

def group_scanner(log_queue, count_queue, proxy_iter, gid_ranges, gid_cutoff, gid_chunk_size, timeout=5):
    """De hoofd-scanner thread."""
    print("[ SCANNER ] Thread succesvol opgestart!")
    
    for start_id, end_id in gid_ranges:
        current_id = start_id
        while current_id <= end_id:
            chunk = []
            for i in range(gid_chunk_size):
                if current_id + i <= end_id:
                    chunk.append(current_id + i)
            
            if not chunk:
                break
                
            try:
                auth, proxy_addr = next(proxy_iter)
                
                # Simpel batch-verzoek naar Roblox API via proxy
                ids_str = ",".join(map(str, chunk))
                url = f"https://groups.roblox.com/v1/groups?groupIds={ids_str}"
                
                proxies = {
                    "http": f"http://{proxy_addr[0]}:{proxy_addr[1]}",
                    "https": f"http://{proxy_addr[0]}:{proxy_addr[1]}"
                }
                
                response = requests.get(url, timeout=timeout, proxies=proxies)
                
                if response.status_code == 200:
                    data = response.json()
                    found_groups = data.get("data", [])
                    
                    # Geef door hoeveel we er gescand hebben
                    count_queue.put([(time.time(), len(chunk))])
                    
                    for group in found_groups:
                        # Als er geen eigenaar is, sturen we het groeps-ID door!
                        if group.get("owner") is None:
                            log_queue.put(group.get("id"))
                            
                elif response.status_code == 429:
                    time.sleep(2)
                    
            except Exception:
                # Bij een proxy-fout gaan we direct geruisloos door
                pass
                
            current_id += gid_chunk_size
