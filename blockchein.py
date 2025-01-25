import time

def simple_hash(data):
    """
    Қарапайым хэш функциясының өз қолымызбен жазылған нұсқасы.
    Кіріс деректерін ерекше (бірақ қауіпсіз емес) хэшке айналдырады.
    """
    hash_value = 0
    prime = 31  # Қақтығыстарды азайту үшін кішкене жай сан

    for i, char in enumerate(data):
        # Әріптің ASCII мәнін және орнын пайдаланып хэш есептеу
        hash_value += (ord(char) * (i + 1))
        # Қиындық қосу үшін жай санмен араластыру
        hash_value = hash_value * prime

    # Хэш өлшемін нақты ауқымда шектеу (мысалы, 32-биттік бүтін сан)
    hash_value = hash_value & 0xFFFFFFFF

    return hash_value

class Block:
    """
    Блок құрылымын сипаттайтын класс.
    """
    def __init__(self, previous_hash, data):
        self.timestamp = time.time()  # Уақыт таңбасы
        self.previous_hash = previous_hash  # Алдыңғы блоктың хэші
        self.data = data  # Блок деректері
        self.hash = self.calculate_hash()  # Блоктың хэші

    def calculate_hash(self):
        """
        Блок деректерінің хэшін есептейді.
        """
        hash_data = f"{self.timestamp}{self.previous_hash}{self.data}"
        return simple_hash(hash_data)

class Blockchain:
    """
    Блоктардың тізбегін сипаттайтын блокчейн класы.
    """
    def __init__(self):
        self.chain = [self.create_genesis_block()]

    def create_genesis_block(self):
        """
        Генезис блогын жасайды.
        """
        return Block("0", "Генезис блогы")

    def add_block(self, data):
        """
        Жаңа блок қосады.
        """
        previous_block = self.chain[-1]
        new_block = Block(previous_block.hash, data)
        self.chain.append(new_block)

    def is_valid_chain(self):
        """
        Блокчейнді тексереді.
        """
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]

            # Алдыңғы хэшті тексеру
            if current_block.previous_hash != previous_block.hash:
                return False

            # Блоктың хэшін тексеру
            if current_block.hash != current_block.calculate_hash():
                return False

        return True

# Блокчейнді тестілеу
if __name__ == "__main__":
    blockchain = Blockchain()
    blockchain.add_block("Екінші блок")
    blockchain.add_block("Үшінші блок")

    print("Блокчейн мәліметтері:")
    for block in blockchain.chain:
        print(f"Уақыт таңбасы: {block.timestamp}")
        print(f"Алдыңғы блоктың хэші: {block.previous_hash}")
        print(f"Деректер: {block.data}")
        print(f"Хэш: {block.hash}")
        print("---")

    # Валидацияны тексеру
    print("Блокчейн дұрыс па?")
    print(blockchain.is_valid_chain())
