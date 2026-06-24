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


if __name__ == "__main__":
    multiprocessing.freeze_support()

    # Zorg dat er automatisch een proxy-bestand wordt aangemaakt als die er niet is
    if not os.path.exists('proxies.txt'):
        get_content_from_sources()

    # Hier passen we de instellingen aan voor Render (laag geheugenverbruik)
    sys.argv = [
        sys.argv[0], 
        "--workers", "1",      # Maximaal 1 proces (bespaart enorm veel RAM)
        "--threads", "4",      # 4 lichte threads binnen dat proces
        "--proxy-file", "proxies.txt",
        "--chunk-size", "50"   # Kleinere batches sturen per keer
    ]

    args = parse_args()
    try:
        Controller(args)
    except KeyboardInterrupt:
        pass
