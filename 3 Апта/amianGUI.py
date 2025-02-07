import time
import tkinter as tk
from tkinter import messagebox, filedialog
import json

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

# ===== Қарапайым Хэш Функциясы =====
def simple_hash(data):
    """Қарапайым хэш функциясы."""
    hash_value = 0
    prime = 31  # Хэшті тұрақты ету үшін жай сан
    for i, char in enumerate(data):
        hash_value += (ord(char) * (i + 1))
        hash_value = hash_value * prime
    return hash_value & 0xFFFFFFFF  # 32-бит шектеу

# ===== Wallets (әмияндар) және Аккаунт Адрестері =====
# Аккаунттың адресі ретінде ашық кілттің хэші пайдаланылады.
wallets = {}

def create_wallet(name, p, q):
    """
    name - пайдаланушы аты,
    p, q - RSA үшін таңдалған жай сандар.
    Әмиян құрылып, ашық кілттің хэшінен аккаунт адресі есептеледі.
    """
    public_key, private_key = generate_keypair(p, q)
    address = simple_hash(str(public_key))
    wallet = {
        'name': name,
        'public_key': public_key,
        'private_key': private_key,
        'address': address
    }
    wallets[address] = wallet
    return wallet

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
        """
        sender, receiver - аккаунт адресі (ашық кілттің хэші),
        amount, fee - сома және комиссия,
        utxo_model - UTXO моделі арқылы баланс тексеріледі.
        """
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.fee = fee
        self.valid = utxo_model.update_balance(sender, receiver, amount, fee)
        self.tx_hash = self.calculate_hash()
        self.signature = None
        if self.valid and self.sender in wallets:
            private_key = wallets[self.sender]['private_key']  # (d, n)
            n = private_key[1]
            self.signature = pow(self.tx_hash % n, private_key[0], n)
    
    def calculate_hash(self):
        return simple_hash(f"{self.sender}{self.receiver}{self.amount}{self.fee}")
    
    def verify_signature(self):
        """Цифрлық қолтаңбаның жарамдылығын ашық кілт арқылы тексеру."""
        if self.signature is None or self.sender not in wallets:
            return False
        public_key = wallets[self.sender]['public_key']  # (e, n)
        n = public_key[1]
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
        valid_transactions = [tx for tx in transactions if tx.valid and tx.verify_signature()]
        if not valid_transactions:
            print("Жарамсыз транзакциялар, блок қосылмады.")
            return False
        previous_block = self.chain[-1]
        new_block = Block(previous_block.hash, valid_transactions)
        self.chain.append(new_block)
        return True
    
    def is_valid_chain(self):
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

# Алдын ала мысал транзакциялары (бұл блок эксплорерінде көрсетіледі)
transactions1 = [
    Transaction(create_wallet("Alice", 61, 53)['address'], create_wallet("Bob", 47, 43)['address'], 10, 0.1, utxo_model),
    Transaction(create_wallet("Bob", 47, 43)['address'], create_wallet("Charlie", 59, 53)['address'], 5, 0.05, utxo_model)
]
transactions2 = [
    Transaction(create_wallet("Charlie", 59, 53)['address'], create_wallet("Dave", 61, 59)['address'], 15, 0.2, utxo_model),
    Transaction(create_wallet("Alice", 61, 53)['address'], create_wallet("Eve", 67, 61)['address'], 200, 0.3, utxo_model)
]

blockchain.add_block(transactions1)
blockchain.add_block(transactions2)

# ===== GUI Интерфейсі =====

root = tk.Tk()
root.title("Блок Эксплорер және Әмиян")

# Әмиян басқару интерфейсі
wallet_frame = tk.Frame(root, bd=2, relief="groove")
wallet_frame.pack(padx=10, pady=10, fill="x")

tk.Label(wallet_frame, text="Әмиян Басқару", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=4, pady=5)

# Әмиян құру үшін өрістер
tk.Label(wallet_frame, text="Аты:").grid(row=1, column=0, sticky="e")
entry_name = tk.Entry(wallet_frame)
entry_name.grid(row=1, column=1, padx=5)

tk.Label(wallet_frame, text="p:").grid(row=1, column=2, sticky="e")
entry_p = tk.Entry(wallet_frame, width=5)
entry_p.grid(row=1, column=3, padx=5)
entry_p.insert(0, "61")

tk.Label(wallet_frame, text="q:").grid(row=2, column=0, sticky="e")
entry_q = tk.Entry(wallet_frame, width=5)
entry_q.grid(row=2, column=1, padx=5)
entry_q.insert(0, "53")

def create_wallet_gui():
    name = entry_name.get()
    try:
        p = int(entry_p.get())
        q = int(entry_q.get())
    except ValueError:
        messagebox.showerror("Қате", "p және q бүтін сандар болуы тиіс.")
        return
    wallet = create_wallet(name, p, q)
    messagebox.showinfo("Әмиян құрылды", f"Аты: {wallet['name']}\nАдрес: {wallet['address']}\nАшық кілт: {wallet['public_key']}\nЖеке кілт: {wallet['private_key']}")
    update_wallet_list()

btn_create_wallet = tk.Button(wallet_frame, text="Әмиян құру", command=create_wallet_gui)
btn_create_wallet.grid(row=2, column=2, columnspan=2, padx=5, pady=5)

# Әмияндарды көрсету (жеңіл түрде тізім ретінде)
wallet_listbox = tk.Listbox(wallet_frame, width=80)
wallet_listbox.grid(row=3, column=0, columnspan=4, pady=5)

def update_wallet_list():
    wallet_listbox.delete(0, tk.END)
    for addr, wallet in wallets.items():
        wallet_listbox.insert(tk.END, f"Адрес: {addr} | Аты: {wallet['name']}")

btn_show_wallets = tk.Button(wallet_frame, text="Әмияндарды жаңарту", command=update_wallet_list)
btn_show_wallets.grid(row=4, column=0, columnspan=4, pady=5)

def save_wallet():
    # Таңдалған әмиянды файлға сақтау (суық әмиян)
    selection = wallet_listbox.curselection()
    if not selection:
        messagebox.showerror("Қате", "Сақтау үшін әмиянды таңдаңыз.")
        return
    index = selection[0]
    wallet_info = wallet_listbox.get(index)
    addr = wallet_info.split("|")[0].split(":")[1].strip()
    wallet = wallets.get(int(addr))
    if wallet is None:
        messagebox.showerror("Қате", "Әмиян табылмады.")
        return
    filename = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
    if filename:
        with open(filename, "w") as f:
            json.dump(wallet, f)
        messagebox.showinfo("Сақталды", f"Әмиян файлға сақталды: {filename}")

def load_wallet():
    filename = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
    if filename:
        with open(filename, "r") as f:
            wallet = json.load(f)
        # Жүктелген әмиянды wallets-ке қосамыз
        addr = wallet.get("address")
        if addr:
            wallets[addr] = wallet
            update_wallet_list()
            messagebox.showinfo("Жүктелді", f"Әмиян жүктелді: {wallet.get('name')}")
        else:
            messagebox.showerror("Қате", "Әмиян деректері дұрыс емес.")

btn_save_wallet = tk.Button(wallet_frame, text="Суық әмиянды сақтау", command=save_wallet)
btn_save_wallet.grid(row=5, column=0, columnspan=2, pady=5)

btn_load_wallet = tk.Button(wallet_frame, text="Суық әмиянды жүктеу", command=load_wallet)
btn_load_wallet.grid(row=5, column=2, columnspan=2, pady=5)

def show_balances():
    balances = utxo_model.balances
    if not balances:
        messagebox.showinfo("Баланстар", "Әзірге баланс деректері жоқ.")
    else:
        info = "\n".join([f"Адрес: {addr} => Баланс: {bal}" for addr, bal in balances.items()])
        messagebox.showinfo("Баланстар", info)

btn_show_balances = tk.Button(wallet_frame, text="Баланстарды көрсету", command=show_balances)
btn_show_balances.grid(row=6, column=0, columnspan=4, pady=5)

# Транзакция жіберу интерфейсі
tk.Label(wallet_frame, text="Транзакция жіберу", font=("Arial", 12, "bold")).grid(row=7, column=0, columnspan=4, pady=5)

tk.Label(wallet_frame, text="Жіберуші Адрес:").grid(row=8, column=0, sticky="e")
entry_sender = tk.Entry(wallet_frame, width=40)
entry_sender.grid(row=8, column=1, columnspan=3, padx=5, pady=2)

tk.Label(wallet_frame, text="Алушы Адрес:").grid(row=9, column=0, sticky="e")
entry_receiver = tk.Entry(wallet_frame, width=40)
entry_receiver.grid(row=9, column=1, columnspan=3, padx=5, pady=2)

tk.Label(wallet_frame, text="Сома:").grid(row=10, column=0, sticky="e")
entry_amount = tk.Entry(wallet_frame, width=10)
entry_amount.grid(row=10, column=1, padx=5, pady=2)

tk.Label(wallet_frame, text="Комиссия:").grid(row=10, column=2, sticky="e")
entry_fee = tk.Entry(wallet_frame, width=10)
entry_fee.grid(row=10, column=3, padx=5, pady=2)

def send_transaction():
    sender = entry_sender.get().strip()
    receiver = entry_receiver.get().strip()
    try:
        amount = float(entry_amount.get())
        fee = float(entry_fee.get())
    except ValueError:
        messagebox.showerror("Қате", "Сома және комиссия сандық мән болуы тиіс.")
        return
    tx = Transaction(sender, receiver, amount, fee, utxo_model)
    if not tx.valid:
        messagebox.showerror("Қате", "Жіберушіде жеткілікті қаражат жоқ немесе транзакция жарамсыз.")
        return
    if not tx.verify_signature():
        messagebox.showerror("Қате", "Қолтаңба жарамсыз.")
        return
    # Жаңа блок ретінде транзакцияны блокчейнге қосамыз.
    if blockchain.add_block([tx]):
        messagebox.showinfo("Жіберілді", "Транзакция жіберілді және блокқа қосылды.")
        show_blocks()  # блок эксплорерін жаңартамыз
    else:
        messagebox.showerror("Қате", "Транзакция блокқа қосылмады.")

btn_send_tx = tk.Button(wallet_frame, text="Транзакция жіберу", command=send_transaction)
btn_send_tx.grid(row=11, column=0, columnspan=4, pady=5)

# Блок эксплорері (GUI)
explorer_frame = tk.Frame(root, bd=2, relief="groove")
explorer_frame.pack(padx=10, pady=10, fill="both", expand=True)

tk.Label(explorer_frame, text="Блок Эксплорер", font=("Arial", 12, "bold")).pack(pady=5)

def show_blocks():
    for widget in explorer_frame.winfo_children():
        if isinstance(widget, tk.Label) and widget.cget("fg") != "blue":
            widget.destroy()
    for i, block in enumerate(blockchain.chain):
        validity = "✅ Жарамды" if i == 0 or block.previous_hash == blockchain.chain[i-1].hash else "❌ Жарамсыз"
        transactions_info = "\n".join([
            f"Жіберуші: {wallets.get(tx.sender, {}).get('name', tx.sender)} ({tx.sender})\n"
            f"Алушы: {wallets.get(tx.receiver, {}).get('name', tx.receiver)} ({tx.receiver})\n"
            f"Сома: {tx.amount}\n"
            f"Tx Хэш: {tx.tx_hash}\n"
            f"Сигнатура: {tx.signature} ({'жарамды' if tx.verify_signature() else 'жарамсыз'})"
            for tx in block.transactions
        ])
        block_info = (f"Блок {i}\n"
                      f"Хэш: {block.hash}\n"
                      f"Уақыт: {block.timestamp}\n"
                      f"Меркле түбірі: {block.merkle_root}\n"
                      f"Транзакциялар:\n{transactions_info}\n"
                      f"{validity}")
        tk.Label(explorer_frame, text=block_info, padx=10, pady=10, borderwidth=2, relief="solid", font=("Arial", 10)).pack(pady=5, fill="x")

btn_show_blocks = tk.Button(explorer_frame, text="Блоктарды жаңарту", command=show_blocks)
btn_show_blocks.pack(pady=5)

def check_validity():
    if blockchain.is_valid_chain():
        messagebox.showinfo("Блокчейн дұрыстығы", "✅ Блокчейн жарамды!")
    else:
        messagebox.showerror("Блокчейн қатесі", "❌ Блокчейнде қате бар!")

btn_check_validity = tk.Button(explorer_frame, text="Блокчейнді тексеру", command=check_validity)
btn_check_validity.pack(pady=5)

root.mainloop()