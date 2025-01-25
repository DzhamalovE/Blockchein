import hashlib
import time
from datetime import datetime

# Блок құрылымын анықтау
class Block:
    def __init__(self, timestamp, previous_hash, data):
        self.timestamp = timestamp  # Блоктың қосылған уақыты
        self.previous_hash = previous_hash  # Алдыңғы блоктың хэші
        self.data = data  # Блокта сақталатын деректер
        self.hash = self.calculate_hash()  # Блоктың өз хэшін есептеу

    def calculate_hash(self):
        # Хэш функциясын қолдана отырып, блоктың хэшін есептеу
        block_string = str(self.timestamp) + str(self.previous_hash) + str(self.data)
        return hashlib.sha256(block_string.encode('utf-8')).hexdigest()

# Генезис блогын жасау
def create_genesis_block():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Уақытты форматтаймыз
    return Block(timestamp, "0", "Genesis Block")

# Келесі блокты жасау
def create_new_block(previous_block, data):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Уақытты форматтаймыз
    return Block(timestamp, previous_block.hash, data)

# Генезис блогын жасаймыз
genesis_block = create_genesis_block()
print(f"Genesis Block Hash: {genesis_block.hash}")
print(f"Genesis Block Timestamp: {genesis_block.timestamp}")  # Генезис блогының уақыты

# Келесі блокты жасаймыз
new_block = create_new_block(genesis_block, "Some transaction data")
print(f"New Block Hash: {new_block.hash}")
print(f"New Block Timestamp: {new_block.timestamp}")  # Жаңа блоктың уақыты
print(f"Previous Block Hash: {new_block.previous_hash}")
