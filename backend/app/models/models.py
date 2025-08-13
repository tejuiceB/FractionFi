import uuid
from sqlalchemy import Column, String, Float, DateTime, Text, Boolean, ForeignKey, BigInteger, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.sql import func

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    role = Column(String, default="investor")  # investor, issuer, admin
    kyc_status = Column(String, default="pending")  # pending, verified, rejected
    wallet_address = Column(String, unique=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    kyc_documents = relationship("KYCDocument", back_populates="user")
    orders = relationship("Order", back_populates="user")
    holdings = relationship("Holding", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="actor")

class KYCDocument(Base):
    __tablename__ = "kyc_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    doc_type = Column(String, nullable=False)  # aadhar, pan, bank_statement
    doc_path = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending, verified, rejected
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="kyc_documents")

class Bond(Base):
    __tablename__ = "bonds"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    issuer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    isin = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    coupon_rate = Column(Float, nullable=False)
    maturity_date = Column(DateTime, nullable=False)
    face_value = Column(Numeric(precision=20, scale=2), nullable=False)
    min_unit = Column(Numeric(precision=20, scale=2), nullable=False)
    token_contract_address = Column(String, nullable=True)
    total_token_supply = Column(BigInteger, nullable=True)
    status = Column(String, default="draft")  # draft, active, matured
    bond_metadata = Column(JSONB, nullable=True)

    # Relationships
    issuer = relationship("User")
    orders = relationship("Order", back_populates="bond")
    trades = relationship("Trade", back_populates="bond")
    holdings = relationship("Holding", back_populates="bond")
    transactions = relationship("Transaction", back_populates="bond")

class Order(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    bond_id = Column(UUID(as_uuid=True), ForeignKey("bonds.id"), nullable=False)
    side = Column(String, nullable=False)  # buy, sell
    type = Column(String, default="limit")  # limit, market
    price = Column(Numeric(precision=20, scale=2), nullable=False)
    quantity = Column(Numeric(precision=20, scale=2), nullable=False)
    filled_quantity = Column(Numeric(precision=20, scale=2), default=0)
    status = Column(String, default="open")  # open, filled, partial, cancelled
    tx_hash = Column(String, nullable=True)  # Blockchain transaction hash
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="orders")
    bond = relationship("Bond", back_populates="orders")
    buy_trades = relationship("Trade", foreign_keys="[Trade.buy_order_id]", back_populates="buy_order")
    sell_trades = relationship("Trade", foreign_keys="[Trade.sell_order_id]", back_populates="sell_order")

class Trade(Base):
    __tablename__ = "trades"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    buy_order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    sell_order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    bond_id = Column(UUID(as_uuid=True), ForeignKey("bonds.id"), nullable=False)
    price = Column(Numeric(precision=20, scale=2), nullable=False)
    quantity = Column(Numeric(precision=20, scale=2), nullable=False)
    tx_hash = Column(String, nullable=True)  # Blockchain transaction hash for trade execution
    executed_at = Column(DateTime(timezone=True), server_default=func.now())
    tx_hash = Column(String, nullable=True)

    # Relationships
    buy_order = relationship("Order", foreign_keys=[buy_order_id], back_populates="buy_trades")
    sell_order = relationship("Order", foreign_keys=[sell_order_id], back_populates="sell_trades")
    bond = relationship("Bond", back_populates="trades")

class Holding(Base):
    __tablename__ = "holdings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    bond_id = Column(UUID(as_uuid=True), ForeignKey("bonds.id"), nullable=False)
    quantity = Column(Numeric(precision=20, scale=2), nullable=False)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="holdings")
    bond = relationship("Bond", back_populates="holdings")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tx_hash = Column(String, unique=True, nullable=False)
    from_address = Column(String, nullable=False)
    to_address = Column(String, nullable=False)
    bond_id = Column(UUID(as_uuid=True), ForeignKey("bonds.id"), nullable=False)
    token_amount = Column(Numeric(precision=20, scale=2), nullable=False)
    status = Column(String, default="pending")  # pending, confirmed, failed
    block_number = Column(BigInteger, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    bond = relationship("Bond", back_populates="transactions")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    action = Column(String, nullable=False)
    payload = Column(JSONB, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    actor = relationship("User", back_populates="audit_logs")
