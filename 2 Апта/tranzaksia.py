import time
import tkinter as tk
from tkinter import messagebox


def simple_hash(data):
    """Қарапайым хэш функциясы."""
    hash_value = 0
    prime = 31  # Хэшті тұрақты ету үшін жай сан

    for i, char in enumerate(data):
        hash_value += (ord(char) * (i + 1))
        hash_value = hash_value * prime

    return hash_value & 0xFFFFFFFF  # 32-бит шектеу


class Transaction:
    """Транзакция құрылымы."""
    def __init__(self, sender, receiver, amount, fee):
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.fee = fee
        self.tx_hash = self.calculate_hash()

    def calculate_hash(self):
        return simple_hash(f"{self.sender}{self.receiver}{self.amount}{self.fee}")


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
                tx_hashes.append(tx_hashes[-1])  # Егер тақ болса, соңғыны қайталаймыз

            new_level = []
            for i in range(0, len(tx_hashes), 2):
                combined_hash = simple_hash(str(tx_hashes[i]) + str(tx_hashes[i + 1]))
                new_level.append(combined_hash)

            tx_hashes = new_level

        return tx_hashes[0]


class Block:
    """Блок құрылымы."""
    def __init__(self, previous_hash, transactions):
        self.timestamp = time.strftime('%Y-%m-%d %H:%M:%S')  # Уақыт белгісі
        self.previous_hash = previous_hash  # Алдыңғы блоктың хэші
        self.transactions = transactions  # Транзакциялар
        self.merkle_root = MerkleTree(transactions).root  # Меркле түбірі
        self.hash = self.calculate_hash()  # Блоктың хэші

    def calculate_hash(self):
        return simple_hash(f"{self.timestamp}{self.previous_hash}{self.merkle_root}")


class Blockchain:
    """Блокчейн құрылымы."""
    def __init__(self):
        self.chain = [self.create_genesis_block()]

    def create_genesis_block(self):
        return Block("0", [])

    def add_block(self, transactions):
        previous_block = self.chain[-1]
        new_block = Block(previous_block.hash, transactions)
        self.chain.append(new_block)

    def is_valid_chain(self):
        """Блокчейннің дұрыстығын тексеру."""
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]

            if current_block.previous_hash != previous_block.hash:
                return False  # Хэш дұрыс емес

            if current_block.hash != current_block.calculate_hash():
                return False  # Деректер өзгертілген

        return True


# === Блокчейнді құру ===
blockchain = Blockchain()
transactions1 = [Transaction("Alice", "Bob", 10, 0.1), Transaction("Bob", "Charlie", 5, 0.05)]
transactions2 = [Transaction("Charlie", "Dave", 15, 0.2)]
blockchain.add_block(transactions1)
blockchain.add_block(transactions2)


# === GUI Интерфейсі ===
def show_blocks():
    """Блоктарды GUI-да көрсету."""
    for widget in frame.winfo_children():
        widget.destroy()

    for i, block in enumerate(blockchain.chain):
        validity = "✅ Жарамды" if i == 0 or block.previous_hash == blockchain.chain[i - 1].hash else "❌ Жарамсыз"
        transactions_info = "\n".join([f"{tx.sender} → {tx.receiver}: {tx.amount} ({tx.fee} комиссия)" for tx in block.transactions])
        block_info = (f"Блок {i}\nХэш: {block.hash}\nУақыт: {block.timestamp}\n"
                      f"Меркле түбірі: {block.merkle_root}\n"
                      f"Транзакциялар:\n{transactions_info}\n{validity}")
        
        label = tk.Label(frame, text=block_info, padx=10, pady=10, borderwidth=2, relief="solid", font=("Arial", 10))
        label.pack(pady=5, fill="x")


def check_validity():
    """Блокчейннің дұрыстығын тексеру."""
    if blockchain.is_valid_chain():
        messagebox.showinfo("Блокчейн дұрыстығы", "✅ Блокчейн жарамды!")
    else:
        messagebox.showerror("Блокчейн қатесі", "❌ Блокчейнде қате бар!")


# === Негізгі GUI терезесі ===
root = tk.Tk()
root.title("Блок Эксплорер")

frame = tk.Frame(root)
frame.pack(padx=10, pady=10)

show_blocks_button = tk.Button(root, text="Блоктарды көрсету", command=show_blocks)
show_blocks_button.pack(pady=5)

check_validity_button = tk.Button(root, text="Блокчейнді тексеру", command=check_validity)
check_validity_button.pack(pady=5)

root.mainloop()