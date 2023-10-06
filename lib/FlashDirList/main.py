import os
import sys
import socket
import network

BRD = os.uname().machine

def list_files(directory):
    content = """<!DOCTYPE html>
<html>
<head>
    <title>File Explorer</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            padding: 20px;
        }
        ul {
            list-style-type: none;
            padding: 0;
        }
        li {
            display: flex;
            align-items: center;
            margin-bottom: 10px;
        }
        .file-icon, .folder-icon {
            width: 24px;
            height: 24px;
            margin-right: 10px;
        }
        .directory {
            color: #007bff;
            text-decoration: none;
        }
    </style>
</head>
<body>
    <h1>File Explorer</h1>
    <ul>"""

    for item in os.listdir('/flash' + directory):
        item_path = '/flash' + directory + '/' + item
        icon_path = '/folder.png' if os.stat(item_path)[0] & 0x4000 else '/file.png'
        if directory == '/':
            content += f'<li><img class="file-icon" src="{icon_path}" alt="icon"><a class="directory" href="/{item}">{item}</a></li>'
        else:
            content += f'<li><img class="file-icon" src="{icon_path}" alt="icon"><a class="directory" href="{directory}/{item}">{item}</a></li>'

    content += """</ul>
</body>
</html>"""
    return content

def not_found():
    content = "HTTP/1.1 404 Not Found\nContent-Type: text/plain\n\nFile not found"
    return content

# Function to handle incoming HTTP requests
def handle_request(client):
    request = client.recv(1024).decode()
    
    # Extract the requested file path from the request
    file_path = request.split(' ')[1]

    if os.stat('/flash' + file_path)[0] & 0x4000:
        subdirectory = file_path.split('/')[1]
        client.send("HTTP/1.1 200 OK\n")
        client.send("Content-Type: text/html\n")
        client.send("\n")
        client.send(list_files(file_path))
    else:
        print(file_path + ' FILE')
        try:
            with open('/flash' + file_path, 'rb') as file:
                if file_path.endswith('.html'):
                    content_type = 'text/html'
                elif file_path.endswith('.png'):
                    content_type = 'image/png'
                elif file_path.endswith('.jpg') or file_path.endswith('.jpeg'):
                    content_type = 'image/jpeg'
                else:
                    content_type = 'text/plain'

                client.send("HTTP/1.1 200 OK\n")
                client.send("Content-Type: {}\n".format(content_type))
                client.send("\n")
                client.send(file.read())
        except OSError:
            client.send(not_found())
    client.close()

def DEMO():
    if("VK-RA6M5" in BRD):
        Lan = network.LAN()
        print('Taking an IP ...')
        Lan.active(True)        
        addr = (Lan.ifconfig()[0], 80)

        # Create a server socket
        s = socket.socket()
        s.bind(addr)
        s.listen(1) # (5)
        print('Listening on ', addr)

        while True:
            try:
                client, addr = s.accept()
                handle_request(client)
            except Exception as e:
                print("Error:", e)
        s.close()

DEMO()