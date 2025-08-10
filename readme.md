# Tokenized Bond Liquidity Platform — Architecture Diagrams

This README captures the architecture of the platform described (Next.js + FastAPI + PostgreSQL + Ethereum + AI/ML + DPI). Diagrams are rendered with Mermaid on GitHub.


## High‑level system overview

```mermaid
flowchart TB
  U[End User<br/>Investor Issuer Admin]

  subgraph EDGE[Edge / Client]
    FE[Next.js<br/>React UI<br/>Wallet MetaMask WalletConnect<br/>WebSocket subscriber]
  end

  subgraph BE[Backend FastAPI]
    API[REST API<br/>Auth JWT Roles<br/>Order Trade APIs<br/>KYC DPI Adapters<br/>AI LLM Gateway]
    WS[WebSocket Hub<br/>Orderbook Trades Portfolio]
    ME[Matching Engine<br/>price-time priority]
    EL[Blockchain Event Listener<br/>Transfer Mint Coupon]
    JOBS[Background Jobs<br/>Coupons Reconciliation Surveillance]
  end

  subgraph DATA[Data Plane]
    DB[(PostgreSQL)]
    REDIS[(Redis)]
  end

  subgraph WEB3[Web3]
    W3P[Web3 Provider<br/>Infura Alchemy Geth]
    ETH[(Ethereum<br/>Sepolia Mainnet)]
  end

  subgraph AI[AI / ML]
    AIML[Pricing Risk Service]
    LLM[LLM Provider<br/>OpenAI Local]
  end

  subgraph DPI[DPI Integrations]
    DL[DigiLocker]
    AA[Account Aggregator]
    UPI[UPI Sandbox]
  end

  subgraph SEC[Security / Ops]
    VAULT[Vault HSM<br/>Custodial keys]
    MON[Monitoring<br/>Prometheus Grafana]
    SENTRY[Sentry]
  end

  classDef cache fill:#ffe7cc,stroke:#f39c12,color:#3e2723
  class REDIS cache

  U --> FE
  FE --> API
  FE --> WS

  API --> DB
  ME --> DB
  EL --> DB
  JOBS --> DB

  API --> REDIS
  ME --> REDIS

  API --> W3P
  EL --> W3P
  W3P --> ETH

  API --> AIML
  API --> LLM

  API --> DL
  API --> AA
  API --> UPI

  API --> VAULT
  EL --> VAULT
  API --> MON
  API --> SENTRY
  ME --> MON
  EL --> MON
```


## End‑to‑end order lifecycle (sequence)

```mermaid
sequenceDiagram
  autonumber
  participant User as User (Buyer/Seller)
  participant FE as Next.js Frontend
  participant API as FastAPI Backend
  participant DB as PostgreSQL
  participant ME as Matching Engine
  participant W3 as Web3 Provider
  participant ETH as Ethereum
  participant EL as Event Listener

  User->>FE: Place order (buy/sell)
  FE->>API: POST /orders (JWT)
  API->>DB: Insert order (status=open)
  API-->>FE: 201 Created (orderId)
  ME->>DB: Read best opposite orders
  ME->>DB: Create trade, update orders (filled/partial)
  ME->>API: Trigger settlement
  API->>W3: transferFrom/transfer (BondToken)
  W3->>ETH: Broadcast tx
  API->>DB: Insert transaction (pending, tx_hash)
  ETH-->>EL: Transfer event
  EL->>DB: Mark tx confirmed, update holdings
  API-->>FE: WS broadcast orderbook/trade/portfolio updates
```


## Order matching and settlement logic (flow)

```mermaid
flowchart TB
  A[New Order] --> B{Validate<br/>JWT KYC balance}
  B -- fail --> X[Reject 4xx]
  B -- ok --> C[Insert into orders<br/>status open]
  C --> D[Match engine picks order]
  D --> E{Opposite orders exist?}
  E -- no --> H[Wait in book]
  E -- yes --> F[Create trades<br/>price-time priority]
  F --> G{Settlement on-chain?}
  G -- yes --> I[Call transfer transferFrom<br/>BondToken] --> J[Record tx_hash<br/>status pending]
  G -- no --> K[Update off-chain holdings]
  J --> L[Listen for event]
  L --> M[Confirm update holdings]
  K --> M
  M --> N[Update orders<br/>filled cancelled]
  N --> O[Notify via WebSocket]
```


## Smart contracts and on‑chain interactions

```mermaid
flowchart LR
  subgraph Chain[Ethereum]
    BT[BondToken<br/>ERC-20 1400-like]
  end

  subgraph Offchain[Backend]
    API[FastAPI]
    EL[Event Listener]
    VAULT[Vault HSM]
  end

  API --> BT
  EL --> BT
  API --> VAULT
  EL --> VAULT
```
## Database ER diagram (core)

```mermaid
erDiagram
  USERS ||--o{ KYC_DOCUMENTS : submits
  USERS ||--o{ ORDERS : places
  USERS ||--o{ HOLDINGS : owns
  USERS ||--o{ AUDIT_LOGS : triggers

  BONDS ||--o{ ORDERS : has
  BONDS ||--o{ TRADES : results_in
  BONDS ||--o{ HOLDINGS : allocates
  BONDS ||--o{ TRANSACTIONS : emits

  ORDERS ||--o{ TRADES : matched_by
  TRADES }o--|| ORDERS : buy_order
  TRADES }o--|| ORDERS : sell_order

  USERS {
    uuid id PK
    string email
    string hashed_password
    string name
    string role
    string kyc_status
    string wallet_address
    datetime created_at
    datetime updated_at
  }

  KYC_DOCUMENTS {
    uuid id PK
    uuid user_id FK
    string doc_type
    string doc_path
    string status
    datetime submitted_at
  }

  BONDS {
    uuid id PK
    uuid issuer_id FK
    string isin
    string name
    float coupon_rate
    date maturity_date
    decimal face_value
    decimal min_unit
    string token_contract_address
    bigint total_token_supply
    string status
    jsonb metadata
  }

  ORDERS {
    uuid id PK
    uuid user_id FK
    uuid bond_id FK
    string side
    string type
    decimal price
    decimal quantity
    decimal filled_quantity
    string status
    datetime created_at
    datetime updated_at
  }

  TRADES {
    uuid id PK
    uuid buy_order_id FK
    uuid sell_order_id FK
    uuid bond_id FK
    decimal price
    decimal quantity
    datetime executed_at
    string tx_hash
  }

  HOLDINGS {
    uuid id PK
    uuid user_id FK
    uuid bond_id FK
    decimal quantity
    datetime last_updated
  }

  TRANSACTIONS {
    uuid id PK
    string tx_hash
    string from_address
    string to_address
    uuid bond_id FK
    decimal token_amount
    string status
    bigint block_number
    datetime created_at
  }

  AUDIT_LOGS {
    uuid id PK
    uuid actor_id FK
    string action
    jsonb payload
    datetime timestamp
  }
```


## Deployment view (container/Kubernetes)

```mermaid
flowchart LR
  subgraph UserNet[Internet]
    U[Users]
  end

  subgraph K8s[Kubernetes]
    subgraph Ingress
      LB[Ingress LB<br/>TLS WAF]
    end

    subgraph Web
      FE[Deployment frontend<br/>Next.js]
    end

    subgraph API
      BE[Deployment backend<br/>FastAPI]
      WS[WebSocket]
      WKR[Deployment workers<br/>Celery RQ]
      REDIS[(Redis)]
    end

    subgraph Data
      PG[(PostgreSQL<br/>StatefulSet or Managed)]
      VAULT[Vault HSM]
    end

    subgraph Observability
      MON[(Prometheus<br/>Grafana)]
      SENTRY[Sentry]
    end
  end

  subgraph Web3[External]
    W3P[Web3 Provider]
    ETH[(Ethereum)]
  end

  U --> LB --> FE --> BE
  BE --> WS
  BE --> PG
  WKR --> PG
  BE --> REDIS
  WKR --> REDIS
  BE --> VAULT
  WKR --> VAULT
  BE --> MON
  BE --> SENTRY

  BE --> W3P
  W3P --> ETH
```
## Security architecture

```mermaid
flowchart TB
  subgraph IdP[Auth]
    JWT[JWT access refresh]
    RBAC[Role-based Access Control]
  end

  subgraph Secrets[Key Mgmt]
    VAULT[Vault HSM]
    SIGNER[Signer service<br/>custodial ops]
  end

  subgraph Backend[FastAPI]
    API[AuthN AuthZ Rate limit Validation]
    ADMIN[Admin endpoints]
  end

  Client[Next.js SPA] --> API
  API --> JWT
  API --> RBAC
  ADMIN --> SIGNER
  SIGNER --> VAULT

  API --> Client
  API --> AUDIT[(Audit)]
```
## Blockchain settlement (DvP — demo)

```mermaid
sequenceDiagram
  autonumber
  participant Buyer
  participant Seller
  participant API as Backend
  participant BT as BondToken
  participant W3 as Web3 Provider
  participant EL as Event Listener

  Seller->>BT: approve(API/custody, amount)
  Buyer->>API: Place buy order
  API->>API: Match with seller
  API->>W3: transferFrom(Seller, Buyer, amount)
  W3-->>BT: Execute transaction
  BT-->>EL: Transfer event
  EL->>API: Update holdings, mark trade settled
  API-->>Buyer: WS: portfolio updated
  API-->>Seller: WS: portfolio updated
```


## Notes

- GitHub renders Mermaid diagrams automatically. If viewing elsewhere, use a Mermaid-compatible renderer.
- The diagrams map exactly to the SRS/architecture text: components, data flows, contracts, ERD, deployment, and security.
- Adapt service names or add nodes (e.g., CDN, API Gateway) as your deployment evolves.
