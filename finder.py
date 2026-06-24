import multiprocessing
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import shutil
import pyfiglet
import requests
import time
import re
from core.controllers import Controller
from core.arguments import parse_args

# Clear the terminal and get terminal size
os.system('cls' if os.name == 'nt' else 'clear')
columns, rows = shutil.get_terminal_size()

# Generate the ASCII art text using pyfiglet
ascii_text = pyfiglet.figlet_format("Ambatokamer", font="standard")

# Split the ASCII art text into lines
lines = ascii_text.split("\n")

# Calculate the position of each line in the middle of the terminal
positions = []
x = int(columns / 2 - len(max(lines, key=len)) / 2)
for i in range(len(lines)):
    y = int(rows / 2 - len(lines) / 2 + i)
    positions.append(y)

# Move the cursor to the calculated positions and print the text
print("\033[1m\033[32m", end="")
for i in range(len(lines)):
    print(f"\033[{positions[i]};{x}H{lines[i]}")
print("\033[1m\033[35m", end="")
print(f"\033[{positions[-1]+1};{x};{x}H[ MACHINE ] : Ambatokam finder")
print("\033[0m", end="")


def get_content_from_sources():
    """
    Makes HTTP requests to the sources, retrieves the content, parses the content for
    proxy information, removes duplicates, and sorts the proxies.
    """
    sources = [
        'https://raw.githubusercontent.com/BlackSnowDot/proxylist-update-every-minute/main/https.txt',
        'https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-https.txt',
        'https://raw.githubusercontent.com/ErcinDedeoglu/proxies/main/proxies/https.txt',
        'https://raw.githubusercontent.com/officialputuid/KangProxy/KangProxy/https/https.txt',
        'https://raw.githubusercontent.com/saisuiu/Lionkings-Http-Proxys-Proxies/main/free.txt',
        'https://raw.githubusercontent.com/officialputuid/KangProxy/KangProxy/https/https.txt'
    ]

    # Make an HTTP request to each URL and retrieve the content
    content = []
    for url in sources:
        response = requests.get(url)
        content.append(response.text)

    # Parse each page's text individually (bug fix: was searching stringified list)
    proxies = []
    regex = r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+"
    for text in content:
        proxies += re.findall(regex, text)

    proxies = list(set(proxies))
    proxies.sort()

    # Write the proxies to a file
    with open('proxies.txt', 'w') as f:
        for proxy in proxies:
            f.write(proxy + "\n")

    print(f"[+] {len(proxies)} proxies opgeslagen in proxies.txt")
    return proxies
def run_fake_server():
    """Start een mini-webserver zodat Render denkt dat dit een website is en online blijft."""
    from flask import Flask
    import logging
    
    app = Flask(__name__)
    # Schakel irritante logberichten uit
    log = logging.getLogger('wsgi')
    log.setLevel(logging.ERROR)

    @app.route('/')
    def home():
        return "Finder is running!", 200

    # Render geeft automatisch een 'PORT' mee aan de server via omgevingsvariabelen
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def start_background_server():
    import threading
    t = threading.Thread(target=run_fake_server, daemon=True)
    t.start()

if __name__ == "__main__":
    multiprocessing.freeze_support()

    # Start de nep-server voor Render
    print("[ SYSTEM ] Starten van de Keep-Alive server...")
    start_background_server()

    # Zorg dat er automatisch een proxy-bestand wordt aangemaakt
    print("[ SYSTEM ] Proxies ophalen...")
    get_content_from_sources()

    # Instellingen voor Render (laag geheugenverbruik)
    sys.argv = [
        sys.argv[0], 
        "--workers", "1",      
        "--threads", "2",  # Iets verlaagd naar 2 voor extra stabiliteit op Render
        "--proxy-file", "proxies.txt",
        "--chunk-size", "25" # Kleinere chunks om proxy-fouten te voorkomen  
    ]

    args = parse_args()
    print(f"[ SYSTEM ] Scanner starten met instellingen: {args}")
    
    try:
        # Start de controller (dit start de threads)
        controller_instance = Controller(args)
        print("[ SYSTEM ] Controller is actief. Scanner hoort nu te lopen.")
        
        # In plaats van een lege 'while True', printen we elke 30 seconden een heartbeat
        while True:
            time.sleep(30)
            print("[ HEARTBEAT ] De hoofd-app leeft nog...")
            
    except KeyboardInterrupt:
        print("[ SYSTEM ] Script handmatig gestopt.")
