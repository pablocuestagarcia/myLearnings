structure BankAccount where
  owner : String
  balance : Int

def deposit (account : BankAccount) (amount : Int) : Except String BankAccount :=
  if amount <= 0 then
    Except.error "El monto a depositar debe ser positivo."
  else
    Except.ok { account with balance := account.balance + amount }

def withdraw (account : BankAccount) (amount : Int) : Except String BankAccount :=
  if amount <= 0 then
    Except.error "El monto a retirar debe ser positivo."
  else if amount > account.balance then
    Except.error "Fondos insuficientes."
  else
    Except.ok { account with balance := account.balance - amount }

def transfer (from_account to_account : BankAccount) (amount : Int) : Except String (BankAccount × BankAccount) :=
  match withdraw from_account amount with
  | Except.error msg => Except.error msg
  | Except.ok new_from =>
    match deposit to_account amount with
    | Except.error msg => Except.error msg
    | Except.ok new_to => Except.ok (new_from, new_to)

-- Teoremas para demostrar la corrección de nuestras funciones

theorem deposit_correct (account : BankAccount) (amount : Int) (h : amount > 0) :
  deposit account amount = Except.ok { account with balance := account.balance + amount } := by
  unfold deposit
  have h1 : ¬(amount <= 0) := by omega
  simp [h1]

theorem withdraw_correct (account : BankAccount) (amount : Int) (h1 : amount > 0) (h2 : amount ≤ account.balance) :
  withdraw account amount = Except.ok { account with balance := account.balance - amount } := by
  unfold withdraw
  have h3 : ¬(amount <= 0) := by omega
  have h4 : ¬(amount > account.balance) := by omega
  simp [h3, h4]

-- Teorema de conservación de balance
theorem transfer_conserves_balance (from_account to_account new_from new_to : BankAccount) (amount : Int)
  (h : transfer from_account to_account amount = Except.ok (new_from, new_to)) :
  new_from.balance + new_to.balance = from_account.balance + to_account.balance := by
  unfold transfer at h
  split at h
  · contradiction
  · rename_i new_from' heq_withdraw
    split at h
    · contradiction
    · rename_i new_to' heq_deposit
      injection h with h_eq
      have h_from : new_from' = new_from := by injection h_eq
      have h_to : new_to' = new_to := by injection h_eq
      subst h_from h_to
      unfold withdraw at heq_withdraw
      split at heq_withdraw
      · contradiction
      · split at heq_withdraw
        · contradiction
        · injection heq_withdraw with heq_from_state
          unfold deposit at heq_deposit
          split at heq_deposit
          · contradiction
          · injection heq_deposit with heq_to_state
            subst heq_from_state heq_to_state
            simp
            omega
