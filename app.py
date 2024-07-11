from flask import Flask, request, jsonify, render_template
import subprocess
import re

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/hostname')
def hostname():
    run = subprocess.run("hostname", capture_output=True)
    return run.stdout

@app.route('/internet')
def internet():
    ping_internet = subprocess.run(['ping', '8.8.8.8'], capture_output=True, text=True)
    ping_intranet_output = ping_internet.stdout.strip()
    ping_internet_stat = parse_ping_output(ping_intranet_output)
    response = {
            "ping_internet": ping_internet_stat,
        }
    return jsonify(response)

@app.route('/intranet')
def intranet():
    # Get server from the request
    server = request.args.get('server')
    if not server:
        return jsonify({"error": "Server parameter is required"}), 400
    ping_intranet = subprocess.run(['ping', server], capture_output=True, text=True)
    ping_intranet_output = ping_intranet.stdout.strip()
    ping_intranet_stats = parse_ping_output(ping_intranet_output)
    response = {
            "ping_intranet": ping_intranet_stats,
        }
    return jsonify(response)


@app.route('/ipconfig')
def ipconfig():
    run = subprocess.run("ipconfig", capture_output=True)
    return run.stdout

@app.route('/diagnostic')
def diagnostic():
    try:
        # Run hostname command
        host = subprocess.run("hostname", capture_output=True, text=True)
        hostname_output = host.stdout.strip()

        # Run ping to the internet
        ping_internet = subprocess.run(['ping', '8.8.8.8'], capture_output=True, text=True)
        ping_internet_output = ping_internet.stdout.strip()
        ping_internet_stats = parse_ping_output(ping_internet_output)

        # Get server from the request
        server = request.args.get('server')
        if not server:
            return jsonify({"error": "Server parameter is required"}), 400

        # Run ping to the intranet
        ping_intranet = subprocess.run(['ping', server], capture_output=True, text=True)
        ping_intranet_output = ping_intranet.stdout.strip()
        ping_intranet_stats = parse_ping_output(ping_intranet_output)

        # Run ipconfig command
        ipconfig = subprocess.run("ipconfig", capture_output=True, text=True)
        ipconfig_output = ipconfig.stdout.strip()

        # Create the response dictionary
        response = {
            "hostname": hostname_output,
            "ping_internet": ping_internet_stats,
            "ping_intranet": ping_intranet_stats,
            "ipconfig": parse_ipconfig_output(ipconfig_output)
        }

        # Return the response as JSON
        return jsonify(response)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def parse_ping_output(ping_output):
    lines = ping_output.split('\n')
    stats = {
        "sent": 0,
        "received": 0,
        "lost": 0,
        "loss_percentage": 0,
        "minimum": 0,
        "maximum": 0,
        "average": 0
    }

    for line in lines:
        if "Packets: Sent" in line:
            match = re.search(r'Sent = (\d+), Received = (\d+), Lost = (\d+) \((\d+)% loss\)', line)
            if match:
                stats["sent"] = int(match.group(1))
                stats["received"] = int(match.group(2))
                stats["lost"] = int(match.group(3))
                stats["loss_percentage"] = int(match.group(4))
        if "Approximate round trip times" in line:
            match = re.search(r'Minimum = (\d+)ms, Maximum = (\d+)ms, Average = (\d+)ms', lines[lines.index(line) + 1])
            if match:
                stats["minimum"] = int(match.group(1))
                stats["maximum"] = int(match.group(2))
                stats["average"] = int(match.group(3))
    
    return stats

def parse_ipconfig_output(ipconfig_output):
    adapters = []
    current_adapter = {}
    lines = ipconfig_output.split('\n')
    
    for line in lines:
        if line.strip() == '':
            continue
        if line.startswith('Ethernet adapter') or line.startswith('Wireless LAN adapter'):
            if current_adapter:
                adapters.append(current_adapter)
            current_adapter = {"name": line.strip()}
        elif ':' in line:
            key, value = map(str.strip, line.split(':', 1))
            current_adapter[key.replace(' ', '_').lower()] = value
    
    if current_adapter:
        adapters.append(current_adapter)
    
    return adapters

@app.route('/ipconfig_flushdns')
def ipconfig_flushdns():
    run = subprocess.run("ipconfig /flushdns", capture_output=True)
    return run.stdout

if __name__ == '__main__':
    app.run(debug=True)
