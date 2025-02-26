import socket
import threading
import json
import time

# Глобальная переменная для хранения блокчейна
blockchain = []
peers = set()
wallets = {}

# Функция создания нового блока узлом-майнером
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
        mine_new_block([message['transaction']])
    elif message['type'] == 'BALANCE_REQUEST':
        balance = get_balance(message['address'])
        response = {'type': 'BALANCE_RESPONSE', 'balance': balance}
        client_socket.send(json.dumps(response).encode())
    elif message['type'] == 'BLOCKCHAIN_REQUEST':
        response = {'type': 'BLOCKCHAIN_RESPONSE', 'blockchain': blockchain}
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

# Функция создания нового блока (майнинг)
def mine_new_block(transactions):
    prev_hash = blockchain[-1]['hash'] if blockchain else "0"
    new_block = create_block(prev_hash, transactions)
    if add_block(new_block):
        broadcast({'type': 'BLOCK', 'block': new_block})
        print("Новый блок замайнен и добавлен в сеть")

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

# Функция запроса блокчейна у узлов
def request_blockchain():
    for peer in peers:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((peer, 5000))
            message = {'type': 'BLOCKCHAIN_REQUEST'}
            s.send(json.dumps(message).encode())
            response = json.loads(s.recv(4096).decode())
            s.close()
            return response.get('blockchain', [])
        except:
            continue
    return []

# Создание первого блока (генезис-блок)
if len(blockchain) == 0:
    blockchain.append(create_block("0", []))

# Запуск узла сети в отдельном потоке
node_thread = threading.Thread(target=start_node, args=(5000,))
node_thread.start()

# Пример отправки транзакции
time.sleep(5)
new_transaction = {'from': 'Alice', 'to': 'Bob', 'amount': 10}
mine_new_block([new_transaction])

# Пример запроса блокчейна
remote_blockchain = request_blockchain()
print("Удаленный блокчейн:", remote_blockchain)
