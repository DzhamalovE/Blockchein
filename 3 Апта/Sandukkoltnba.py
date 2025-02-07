import time
import tkinter as tk
from tkinter import messagebox

# ===== RSA АСИММЕТРИЯЛЫ ҚЫЛУ ФУНКЦИЯЛАРЫ =====
def gcd(a, b):
    """Екі санның ортақ бөлгішін табу."""
    while b:
        a, b = b, a % b
    return a

def egcd(a, b):
    """Кеңейтілген Эвклид алгоритмі."""
    if a == 0:
        return (b, 0, 1)
    else:
        g, y, x = egcd(b % a, a)
        return (g, x - (b // a) * y, y)

def mod_inverse(a, m):
    """Модульдік кері элементті табу: a * x ≡ 1 (mod m)."""
    g, x, _ = egcd(a, m)
    if g != 1:
        raise Exception("Модульдік кері элемент жоқ.")
    return x % m

def is_prime(n):
    """n санының жай сан екенін тексеру."""
    if n < 2:
        return False
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return False
    return True

def generate_keypair(p, q):
    """
    RSA кілт жұбын генерациялау:
      - p және q: екі жай сан.
      - n = p * q, phi = (p - 1) * (q - 1)
      - Ашық кілт үшін e таңдалады (1 < e < phi, gcd(e, phi) = 1).
      - Жеке кілт d есептеледі: e * d ≡ 1 (mod phi).
    Ашық кілт: (e, n), жеке кілт: (d, n)
    """
    if not (is_prime(p) and is_prime(q)):
        raise ValueError("p және q жай сандар болуы тиіс.")
    if p == q:
        raise ValueError("p және q бір-біріне тең болмауы керек.")
    
    n = p * q
    phi = (p - 1) * (q - 1)
    
    e = 65537  # Әдетте қолданылатын e мәні
    if gcd(e, phi) != 1:
        e = 3
        while gcd(e, phi) != 1:
            e += 2
    d = mod_inverse(e, phi)
    return (e, n), (d, n)

# ===== Wallets (әмияндар) =====
# Әр аккаунтқа жеке RSA кілт жұбы бекітіледі
wallets = {}

def create_wallet(account, p, q):
    public_key, private_key = generate_keypair(p, q)
    wallets[account] = (public_key, private_key)

# Мысалы, әр аккаунт үшін шағын жай сандарды қолданамыз
create_wallet("Alice", 61, 53)    # n = 3233
create_wallet("Bob", 47, 43)      # n = 2021
create_wallet("Charlie", 59, 53)  # n = 3127
create_wallet("Dave", 61, 59)     # n = 3599
create_wallet("Eve", 67, 61)      # n = 4087

# ===== Қарапайым Хэш Функциясы =====
def simple_hash(data):
    """Қарапайым хэш функциясы."""
    hash_value = 0
    prime = 31  # Хэшті тұрақты ету үшін жай сан
    for i, char in enumerate(data):
        hash_value += (ord(char) * (i + 1))
        hash_value = hash_value * prime
    return hash_value & 0xFFFFFFFF  # 32-бит шектеу

# ===== UTXO Моделі =====
class UTXOModel:
    """UTXO моделі: Аккаунт баланстарын сақтау."""
    def __init__(self):
        self.balances = {}
    
    def update_balance(self, sender, receiver, amount, fee):
        if sender not in self.balances:
            self.balances[sender] = 100  # Бастапқы баланс
        if receiver not in self.balances:
            self.balances[receiver] = 100  # Бастапқы баланс
        
        if self.balances[sender] >= amount + fee:
            self.balances[sender] -= (amount + fee)
            self.balances[receiver] += amount
            return True
        return False

    def get_balance(self, account):
        return self.balances.get(account, 100)
    
    def validate_balances(self):
        """Барлық аккаунттардың балансы теріс болмауы тиіс."""
        return all(balance >= 0 for balance in self.balances.values())

# ===== Transaction (Транзакция) Класы =====
class Transaction:
    """Транзакция құрылымы, сандық қолтаңба қосылған."""
    def __init__(self, sender, receiver, amount, fee, utxo_model):
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.fee = fee
        # Балансты жаңарту: жеткілікті қаражат болмаса, транзакция жарамсыз деп белгіленеді.
        self.valid = utxo_model.update_balance(sender, receiver, amount, fee)
        self.tx_hash = self.calculate_hash()
        self.signature = None
        # Егер транзакция жарамды болса, жіберушінің жеке кілтімен транзакция деректеріне қолтаңба қойылады.
        if self.valid and self.sender in wallets:
            private_key = wallets[self.sender][1]  # (d, n)
            n = private_key[1]
            # tx_hash-ты n-ге бөлінетін түрде қолтаңбалаймыз.
            self.signature = pow(self.tx_hash % n, private_key[0], n)
    
    def calculate_hash(self):
        return simple_hash(f"{self.sender}{self.receiver}{self.amount}{self.fee}")
    
    def verify_signature(self):
        """Цифрлық қолтаңбаның жарамдылығын ашық кілт арқылы тексеру."""
        if self.signature is None or self.sender not in wallets:
            return False
        public_key = wallets[self.sender][0]  # (e, n)
        n = public_key[1]
        # Қолтаңбаны ашық кілтпен қайта шешеміз және tx_hash-тың n-ге қалдығымен салыстырамыз.
        decrypted = pow(self.signature, public_key[0], n)
        return decrypted == (self.tx_hash % n)

# ===== Merkle Tree (Меркле ағашы) =====
class MerkleTree:
    """Merkle Tree (Меркле ағашы) құрылымы."""
    def __init__(self, transactions):
        self.transactions = transactions
        self.root = self.build_merkle_root()
    
    def build_merkle_root(self):
        """Меркле түбірін есептеу."""
        if not self.transactions:
            return "Бос"
        
        tx_hashes = [tx.tx_hash for tx in self.transactions]
        while len(tx_hashes) > 1:
            if len(tx_hashes) % 2 != 0:
                tx_hashes.append(tx_hashes[-1])
            new_level = []
            for i in range(0, len(tx_hashes), 2):
                combined_hash = simple_hash(str(tx_hashes[i]) + str(tx_hashes[i + 1]))
                new_level.append(combined_hash)
            tx_hashes = new_level
        return tx_hashes[0]

# ===== Block (Блок) Класы =====
class Block:
    """Блок құрылымы."""
    def __init__(self, previous_hash, transactions):
        self.timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        self.previous_hash = previous_hash
        self.transactions = transactions
        self.merkle_root = MerkleTree(transactions).root
        self.hash = self.calculate_hash()
    
    def calculate_hash(self):
        return simple_hash(f"{self.timestamp}{self.previous_hash}{self.merkle_root}{[tx.tx_hash for tx in self.transactions]}")

# ===== Blockchain (Блокчейн) Класы =====
class Blockchain:
    """Блокчейн құрылымы."""
    def __init__(self):
        self.chain = [self.create_genesis_block()]
    
    def create_genesis_block(self):
        return Block("0", [])
    
    def add_block(self, transactions):
        # Тек жарамды және қолтаңбасы дұрыс транзакцияларды ғана блокқа қосамыз.
        valid_transactions = [tx for tx in transactions if tx.valid and tx.verify_signature()]
        if not valid_transactions:
            print("Жарамсыз транзакциялар, блок қосылмады.")
            return False
        previous_block = self.chain[-1]
        new_block = Block(previous_block.hash, valid_transactions)
        self.chain.append(new_block)
        return True
    
    def is_valid_chain(self):
        """Блокчейннің дұрыстығын тексеру."""
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            if current_block.previous_hash != previous_block.hash:
                return False
            if current_block.hash != current_block.calculate_hash():
                return False
            if MerkleTree(current_block.transactions).root != current_block.merkle_root:
                return False
            for tx in current_block.transactions:
                if not tx.verify_signature():
                    return False
        if not utxo_model.validate_balances():
            return False
        return True

# ===== Блокчейн мен UTXO Моделін Құру =====
utxo_model = UTXOModel()
blockchain = Blockchain()

# Бірінші блок транзакциялары
transactions1 = [
    Transaction("Alice", "Bob", 10, 0.1, utxo_model),
    Transaction("Bob", "Charlie", 5, 0.05, utxo_model)
]

# Екінші блок транзакциялары: 
# Мысалы, "Alice" жеткіліксіз қаражатпен 200 монета жіберуге тырысады, сондықтан ол жарамсыз болады.
transactions2 = [
    Transaction("Charlie", "Dave", 15, 0.2, utxo_model),
    Transaction("Alice", "Eve", 200, 0.3, utxo_model)
]

blockchain.add_block(transactions1)
blockchain.add_block(transactions2)

# ===== GUI Интерфейсі =====
def show_blocks():
    """Блоктарды GUI-да көрсету."""
    for widget in frame.winfo_children():
        widget.destroy()
    
    for i, block in enumerate(blockchain.chain):
        validity = "✅ Жарамды" if i == 0 or block.previous_hash == blockchain.chain[i-1].hash else "❌ Жарамсыз"
        transactions_info = "\n".join([
            f"Жіберуші: {tx.sender}, Алушы: {tx.receiver}, Сома: {tx.amount}, "
            f"Tx Хэш: {tx.tx_hash}, Сигнатура: {tx.signature}, "
            f"{'Сигнатура жарамды' if tx.verify_signature() else 'Сигнатура жарамсыз'}"
            for tx in block.transactions
        ])
        block_info = (f"Блок {i}\n"
                      f"Хэш: {block.hash}\n"
                      f"Уақыт: {block.timestamp}\n"
                      f"Меркле түбірі: {block.merkle_root}\n"
                      f"Транзакциялар:\n{transactions_info}\n"
                      f"{validity}")
        label = tk.Label(frame, text=block_info, padx=10, pady=10, borderwidth=2, relief="solid", font=("Arial", 10))
        label.pack(pady=5, fill="x")

def check_validity():
    """Блокчейннің дұрыстығын тексеру."""
    if blockchain.is_valid_chain():
        messagebox.showinfo("Блокчейн дұрыстығы", "✅ Блокчейн жарамды!")
    else:
        messagebox.showerror("Блокчейн қатесі", "❌ Блокчейнде қате бар!")

root = tk.Tk()
root.title("Блок Эксплорер")

frame = tk.Frame(root)
frame.pack(padx=10, pady=10)

show_blocks_button = tk.Button(root, text="Блоктарды көрсету", command=show_blocks)
show_blocks_button.pack(pady=5)

check_validity_button = tk.Button(root, text="Блокчейнді тексеру", command=check_validity)
check_validity_button.pack(pady=5)

root.mainloop()
