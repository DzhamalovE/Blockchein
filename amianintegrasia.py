import socket
import threading
import json
import time

# Глобальная переменная для хранения блокчейна
blockchain = []
peers = set()
wallets = {}

# Функция создания нового блока
def create_block(prev_hash, transactions):
    block = {
        'timestamp': time.time(),
        'previous_hash': prev_hash,
        'transactions': transactions,
        'hash': hash(str(prev_hash) + str(transactions) + str(time.time()))
    }
    return block

# Функция добавления блока в цепочку
def add_block(block):
    if len(blockchain) == 0 or blockchain[-1]['hash'] == block['previous_hash']:
        blockchain.append(block)
        return True
    return False

# Функция обработки соединений между узлами
def handle_client(client_socket):
    data = client_socket.recv(4096).decode()
    if not data:
        return
    message = json.loads(data)
    if message['type'] == 'BLOCK':
        if add_block(message['block']):
            print("Блок добавлен: ", message['block'])
            broadcast(message, client_socket)
    elif message['type'] == 'PEER':
        peers.add(message['peer'])
    elif message['type'] == 'TRANSACTION':
        print("Получена транзакция: ", message['transaction'])
        new_block = create_block(blockchain[-1]['hash'], [message['transaction']])
        add_block(new_block)
        broadcast({'type': 'BLOCK', 'block': new_block})
    elif message['type'] == 'BALANCE_REQUEST':
        balance = get_balance(message['address'])
        response = {'type': 'BALANCE_RESPONSE', 'balance': balance}
        client_socket.send(json.dumps(response).encode())
    client_socket.close()

# Функция отправки данных всем узлам сети
def broadcast(message, exclude_socket=None):
    for peer in peers:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((peer, 5000))
            s.send(json.dumps(message).encode())
            s.close()
        except:
            continue

# Функция запуска узла сети
def start_node(port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", port))
    server.listen(5)
    print(f"Узел запущен на порту {port}")
    while True:
        client_socket, _ = server.accept()
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()

# Создание первого блока (генезис-блок)
if len(blockchain) == 0:
    blockchain.append(create_block("0", []))

# Запуск узла сети в отдельном потоке
node_thread = threading.Thread(target=start_node, args=(5000,))
node_thread.start()

# Симуляция добавления нового блока
time.sleep(5)
new_block = create_block(blockchain[-1]['hash'], [{'from': 'Alice', 'to': 'Bob', 'amount': 10}])
add_block(new_block)
broadcast({'type': 'BLOCK', 'block': new_block})

# Функция отправки транзакции в сеть
def send_transaction(transaction):
    message = {'type': 'TRANSACTION', 'transaction': transaction}
    broadcast(message)

# Функция проверки баланса
def get_balance(address):
    balance = 0
    for block in blockchain:
        for tx in block['transactions']:
            if tx['to'] == address:
                balance += tx['amount']
            if tx['from'] == address:
                balance -= tx['amount']
    return balance

# Функция запроса баланса у узлов
def request_balance(address):
    for peer in peers:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((peer, 5000))
            message = {'type': 'BALANCE_REQUEST', 'address': address}
            s.send(json.dumps(message).encode())
            response = json.loads(s.recv(4096).decode())
            s.close()
            return response.get('balance', 0)
        except:
            continue
    return 0

# Пример отправки транзакции
time.sleep(5)
send_transaction({'from': 'Bob', 'to': 'Charlie', 'amount': 15})

# Пример запроса баланса
address = 'Charlie'
balance = request_balance(address)
print(f"Баланс {address}: {balance}")
