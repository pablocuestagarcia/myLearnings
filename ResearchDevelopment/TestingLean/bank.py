class BankAccount:
    def __init__(self, owner: str, balance: int = 0):
        self.owner = owner
        self.balance = balance

    def deposit(self, amount: int) -> int:
        if amount <= 0:
            raise ValueError("El monto a depositar debe ser positivo.")
        self.balance += amount
        return self.balance

    def withdraw(self, amount: int) -> int:
        if amount <= 0:
            raise ValueError("El monto a retirar debe ser positivo.")
        if amount > self.balance:
            raise ValueError("Fondos insuficientes.")
        self.balance -= amount
        return self.balance

def transfer(from_account: BankAccount, to_account: BankAccount, amount: int) -> None:
    from_account.withdraw(amount)
    to_account.deposit(amount)
