import hashlib
import time
import random

class Blockchain:
    def __init__(self):
        self.chain = []
        self.transactions = []
        self.create_block(proof=1, previous_hash='0')  # Генезис блогын құру
        self.reward = 10  # Минерге берілетін жүлде
        self.commission = 1  # Әр транзакциядан алынатын комиссия

    def create_block(self, proof, previous_hash, miner_address):
        # Транзакция комиссиясын есептеу
        total_fees = len(self.transactions) * self.commission
        reward_transaction = {"sender": "network", "recipient": miner_address, "amount": self.reward + total_fees}
        self.transactions.append(reward_transaction)

        block = {
            'index': len(self.chain) + 1,
            'timestamp': time.time(),
            'transactions': self.transactions,
            'proof': proof,
            'previous_hash': previous_hash
        }
        self.transactions = []
        self.chain.append(block)
        return block

    def add_transaction(self, sender, recipient, amount):
        self.transactions.append({'sender': sender, 'recipient': recipient, 'amount': amount})

    def proof_of_work(self, last_proof):
        proof = 0
        while not self.valid_proof(last_proof, proof):
            proof += 1
        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"  # 4 нөлдік қиындық деңгейі

    def get_last_block(self):
        return self.chain[-1]

# Минерлердің бәсекелестік сценарийі
blockchain = Blockchain()
miners = ["Alice", "Bob"]

def mining_simulation():
    last_proof = blockchain.get_last_block()['proof']
    results = {}

    for miner in miners:
        start_time = time.time()
        proof = blockchain.proof_of_work(last_proof)
        duration = time.time() - start_time
        results[miner] = (proof, duration)
        print(f"{miner} тапқан nonce: {proof}, уақыты: {duration:.2f} секунд")

    winner = min(results, key=lambda x: results[x][1])  # Ең жылдам тапқан майнер
    print(f"\nЖеңімпаз: {winner} ({results[winner][1]:.2f} сек)\n")

    new_block = blockchain.create_block(results[winner][0], blockchain.get_last_block()['previous_hash'], winner)
    print(f"Жаңа блок жасалды: {new_block}\n")

# Транзакциялар қосу
blockchain.add_transaction("User1", "User2", 50)
blockchain.add_transaction("User3", "User4", 20)

# Миннингті бастау
mining_simulation()
