# Clearance

A financial transaction risk engine that intercepts every transfer before money moves, evaluates it against an AI reasoning layer, and either clears or blocks it — atomically. All decisions are persisted in a tamper-evident audit trail.

---

## Problem

Fraud detection in payment systems is traditionally bolt-on: a rule engine sitting downstream of the ledger, flagging transactions after they have already settled. Reversing a committed transfer is expensive, legally complicated, and often impossible. Clearance solves this by making risk assessment a pre-condition of settlement — the AI evaluates each transaction, and the ledger only mutates if the evaluation approves it.

---

## How It Works

```
POST /transfer
       |
       v
  Validate request
  (accounts exist, sufficient funds)
       |
       v
  AI Risk Assessment          <-- transaction is blocked here if flagged
  (Claude Haiku via Anthropic API)
       |
   approve / block
       |
       v (approve only)
  Atomic balance mutation
  + Transaction record commit
  (single SQLAlchemy session, PostgreSQL ACID transaction)
       |
       v
  Response returned
```

The critical property: **no balance change occurs before the risk score is resolved**. If the AI returns `block`, the HTTP handler raises before any database write. If the AI call itself fails, the transaction is not committed. Money does not move unless every preceding gate passes.

---

## AI Risk Scoring Architecture

Claude is used as a structured reasoning component, not as a product surface. It receives three inputs — sender balance, receiver balance, and transfer amount — and returns a deterministic JSON payload:

```json
{
  "risk_score": 0-100,
  "reasoning": "brief explanation",
  "decision": "approve" | "block"
}
```

The model used is `claude-haiku-4-5-20251001` (Claude Haiku), chosen deliberately: it is the fastest and cheapest model in the Claude family, appropriate for synchronous per-transaction evaluation where latency directly degrades user experience. Haiku has sufficient reasoning capability for structured financial risk decisions of this scope.

### Why Claude and not a rule engine

Rule engines encode what engineers already know. They are brittle against novel patterns and require explicit maintenance as fraud evolves. Claude evaluates context — for example, a transfer of 95% of an account's balance is not inherently fraudulent, but it may be when combined with a large absolute value or an unusual receiver balance. The model reasons across the combination of signals rather than checking thresholds in isolation.

### Why Claude is a valve, not the product

The AI layer has a single, bounded responsibility: return a structured decision given structured inputs. It does not own the transaction lifecycle, does not touch the database, and cannot be manipulated through the transfer payload. The pipeline is deterministic around it — if Claude approves, the ledger mutates; if Claude blocks or errors, it does not. This makes the system auditable and the AI component replaceable without touching business logic.

---

## ACID Compliance and Atomicity

Clearance uses PostgreSQL with SQLAlchemy's session management to guarantee that every transfer is fully atomic.

The transfer operation is a two-row mutation: decrement sender balance, increment receiver balance. These two writes must succeed or fail together. If the process crashes, the network drops, or an exception is raised after one write but before the other, a non-atomic system leaves the ledger in a corrupt state — money has vanished or been created.

SQLAlchemy's `db.commit()` sends both mutations in a single transaction to PostgreSQL. PostgreSQL's ACID guarantees ensure:

- **Atomicity** — both writes commit together or neither does
- **Consistency** — foreign key constraints and balance integrity are enforced at the database layer
- **Isolation** — concurrent transfers against the same account are serialised by the database, not application code
- **Durability** — once committed, the transaction survives process restarts

The risk assessment gate sits entirely before `db.commit()`. If the AI blocks the transfer, the session is discarded without writing anything. There is no partial state.

---

## Data Model

```
users
  user_id    INTEGER PRIMARY KEY
  user_name  VARCHAR
  email      VARCHAR UNIQUE

accounts
  account_id INTEGER PRIMARY KEY
  user_id    INTEGER FK -> users.user_id
  balance    INTEGER  (stored in pence; no floating-point arithmetic)

transactions
  transaction_id   INTEGER PRIMARY KEY
  from_account_id  INTEGER FK -> accounts.account_id
  to_account_id    INTEGER FK -> accounts.account_id
  amount           INTEGER
  date_time        DATETIME
  status           VARCHAR  ("approved" | "blocked")
```

Balances are stored as integers in pence. Floating-point currency arithmetic introduces rounding errors that accumulate across a ledger at scale. Integer pence arithmetic is exact.

---

## API Reference

### POST /users

Create a user.

**Request body**
```json
{
  "user_name": "string",
  "email": "string"
}
```


**Response**
```json
{
  "user_id": 1,
  "user_name": "Jane Smith",
  "email": "jane@example.com"
}
```

---

### POST /accounts

Create an account linked to an existing user.

**Request body**
```json
{
  "user_id": 1,
  "balance": 100000
}
```

`balance` is in pence (100000 = £1000.00).

**Response**
```json
{
  "account_id": 1,
  "balance": 100000
}
```

---

### POST /transfer

Process a transfer between two accounts. Triggers AI risk scoring. Blocked transfers return HTTP 400 and do not mutate the ledger.

**Request body**
```json
{
  "from_account_id": 1,
  "to_account_id": 2,
  "amount": 5000
}
```

**Response (approved)**
```json
{
  "transaction_id": 42,
  "status": "success"
}
```

**Response (blocked)**
```
HTTP 400 — Transaction flagged, please contact bank.
```

---

### GET /accounts/{id}/balance

Read the current balance of an account. No side effects.

**Response**
```json
{
  "account_id": 1,
  "balance": 95000
}
```

---

### GET /accounts/{id}/history

Return all transactions where the account was either the sender or receiver, including the AI risk decision recorded at time of processing.

**Response**
```json
[
  {
    "transaction_id": 42,
    "from_account_id": 1,
    "to_account_id": 2,
    "amount": 5000,
    "date_time": "2026-04-20T14:32:00",
    "status": "approved"
  }
]
```

---

## Local Setup

### Requirements

- Python 3.10+
- PostgreSQL running locally (or via Docker)
- An Anthropic API key

### Without Docker

**1. Clone and install dependencies**

```bash
git clone <repo-url>
cd clearance
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**2. Configure environment**

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/clearance
ANTHROPIC_API_KEY=sk-ant-...
```

**3. Create the database**

```bash
createdb clearance
```

Tables are created automatically on startup via `Base.metadata.create_all`.

**4. Run the server**

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

---

### With Docker

**1. Configure environment**

Create a `.env` file:

```env
DATABASE_URL=postgresql://user:password@db:5432/clearance
ANTHROPIC_API_KEY=sk-ant-...
```

**2. Build and run**

```bash
docker build -t clearance .
docker run --env-file .env -p 8000:8000 clearance
```

If running PostgreSQL in a separate container, ensure both containers share a Docker network and the `DATABASE_URL` hostname resolves to the database container.

---

## Tech Stack

| Component | Technology |
|---|---|
| Web framework | FastAPI |
| ORM | SQLAlchemy |
| Database | PostgreSQL |
| Schema validation | Pydantic |
| AI risk layer | Anthropic Claude Haiku (`claude-haiku-4-5-20251001`) |
| Runtime | Python 3.10 |
| Container | Docker |
| Hosting | Render |

---

## Project Scope

Clearance is a backend engineering project. It is not a tutorial, a scaffold, or a demo. The goal was to build a system with production-relevant properties: ACID-compliant financial transactions, a pre-settlement fraud gate, an embedded AI component with a clearly bounded role, and a persistent audit trail. The architecture decisions — integer pence storage, atomic commit placement, AI-as-valve rather than AI-as-product, structured JSON output enforcement — reflect how these systems are built at production scale, not how they are explained in introductory content.
