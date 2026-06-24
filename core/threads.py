import time
import requests
from queue import Empty
from .detection import check_group, check_games, groupimage  
from .utils import make_http_socket, parse_batch_response, json_dumps

def stat_updater(count_queue):
    """Keeping track of the number of groups scanned per second."""
    total_scanned = 0
    start_time = time.time()
    
    while True:
        try:
            chunks = count_queue.get()
            for ts, count in chunks:
                total_scanned += count
            
            elapsed = time.time() - start_time
            if elapsed >= 10:  # Elke 10 seconden een update
                speed = total_scanned / elapsed
                print(f"[ STATS ] Totaal gescand: {total_scanned} | Snelheid: {speed:.2f} groepen/sec")
                total_scanned = 0
                start_time = time.time()
        except Exception as e:
            print(f"[ STATS ERROR ] {e}")
        time.sleep(1)

def log_notifier(log_queue, webhook_url):
    """Stuurt gevonden groepen door naar je Discord/Guilded Webhook."""
    while True:
        try:
            # Wacht op een succesvolle vondst uit de queue
            group_info = log_queue.get()
            print(f"[ HIT! ] Groep gevonden: {group_info.get('id')} - {group_info.get('name')}")
            
            if webhook_url:
                # Maak een mooie Discord embed
                payload = {
                    "embeds": [{
                        "title": f"🎉 Groep Zonder Eigenaar Gevonden!",
                        "url": f"https://www.roblox.com/groups/{group_info.get('id')}",
                        "color": 3066993,  # Groen
                        "fields": [
                            {"name": "Groep ID", "value": str(group_info.get('id')), "inline": True},
                            {"name": "Naam", "value": group_info.get('name'), "inline": True},
                            {"name": "Leden", "value": str(group_info.get('memberCount', 0)), "inline": True}
                        ],
                        "footer": {"text": "Ambatokam Finder"}
                    }]
                }
                
                # Stuur naar de webhook
                requests.post(webhook_url, json=payload, timeout=5)
        except Exception as e:
            print(f"[ WEBHOOK ERROR ] {e}")
        time.sleep(0.5)

def group_scanner(log_queue, count_queue, proxy_iter, gid_ranges, gid_cutoff, gid_chunk_size, timeout=5):
    """De scanner die door de ID-ranges loopt en groepen controleert."""
    print("[ SCANNER ] Thread gestart...")
    
    for start_id, end_id in gid_ranges:
        current_id = start_id
        while current_id <= end_id:
            chunk = []
            # Bouw een batch van IDs om in één keer te checken (sneller!)
            for i in range(gid_chunk_size):
                if current_id + i <= end_id:
                    chunk.append(current_id + i)
            
            if not chunk:
                break
                
            try:
                # Pak de volgende proxy uit de lijst
                auth, proxy_addr = next(proxy_iter)
                
                # Maak een snelle HTTP verbinding via een socket
                # We vragen de groepsdetails op bij de Roblox API
                headers = {"User-Agent": "Roblox/WinInet", "Content-Type": "application/json"}
                ids_str = ",".join(map(str, chunk))
                url = f"https://groups.roblox.com/v1/groups?groupIds={ids_str}"
                
                # Stuur het verzoek via de proxy
                response = requests.get(url, headers=headers, timeout=timeout, proxies={
                    "http": f"http://{proxy_addr[0]}:{proxy_addr[1]}",
                    "https": f"http://{proxy_addr[0]}:{proxy_addr[1]}"
                })
                
                if response.status_code == 200:
                    data = response.json()
                    found_groups = data.get("data", [])
                    
                    # Log het aantal gescande groepen voor stat_updater
                    count_queue.put((time.time(), len(chunk)))
                    
                    for group in found_groups:
                        # Als 'owner' leeg (null) is, is de groep claimbaar!
                        if group.get("owner") is None:
                            # Stuur de hit naar de log_notifier queue
                            log_queue.put(group)
                            
                elif response.status_code == 429:
                    # Rate limit, even rustig aan met deze proxy
                    time.sleep(1)
                    
            except Exception:
                # Proxy error of time-out, ga gewoon door naar de volgende proxy
                pass
                
            current_id += gid_chunk_size
