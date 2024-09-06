"""
Define the database metadata.
Run this file to verify database metadata.
"""
# Standard Imports
from __future__ import annotations
from typing import List, Tuple, Optional
# Third Party Imports
from sqlalchemy import Table, ForeignKey, String, create_engine, Column, Integer, Float, String, DECIMAL
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker, Session
# Project-Specific Imports
from path_management.base import get_database_path


DATABASE_FILE = get_database_path()
class Base(DeclarativeBase): pass


# Association Tables ---------------------------------------------------------- 
# Many-to-many relationships - e.g., a user can be in multiple groups, and a 
# group consists of multiple users.
user_groups = Table(
    'user_groups',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.user_id'), primary_key=True),
    Column('group_id', Integer, ForeignKey('groups.group_id'), primary_key=True)
)

user_items = Table(
    'user_items',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.user_id'), primary_key=True),
    Column('item_id', Integer, ForeignKey('items.item_id'), primary_key=True),
    Column('weight', Float, nullable=True),  # Optional for precise splitting
    Column('quantity', Integer, nullable=True)
)


# Data Tables -----------------------------------------------------------------
class Group(Base):
    """
    SQLALchemy Database entry object.

    Args:
        id (int): Group ID as the primary key. Autoincremented.
        group_name (VARCHAR(20)): Name of the group
        description(VARCHAR(50)): Description of the group, such as rules.
    """
    
    __tablename__ = "groups"
    
    # ----- Columns ----- 
    group_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    group_name: Mapped[str] = mapped_column(String(10), unique=True)  # VARCHAR(20)
    description: Mapped[str] = mapped_column(String(50))  # VARCHAR(50)
    
    
    # ----- Relationships -----
    # A group can have multiple users
    users: Mapped[List["User"]] = relationship("User", secondary=user_groups, back_populates="groups")
    # A group can have multiple receipts
    receipts: Mapped[List["Receipt"]] = relationship("Receipt", back_populates="group")
    
    # ----- Methods -----
    def __repr__(self) -> str:
        return f"Group(id={self.group_id!r}, name = {self.name!r}, description = {self.description!r})"
    

class User(Base):
    
    __tablename__ = "users"
    
    # ----- Columns -----
    user_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(10))
    # password_hashed: Mapped[str] = mapped_column(String(50))
    
    # ----- Relationships -----
    # A user can join multiple groups
    groups: Mapped[List[Group]] = relationship("Group", secondary=user_groups, back_populates="users")
    # A user can have multiple items
    items: Mapped[List[Item]] = relationship("Item", secondary=user_items, back_populates="users")
    
    # ----- Methods -----
    def __repr__(self) -> str:
        return f"User"


class Receipt(Base):
    
    __tablename__ = "receipts"
    
    # ----- Columns -----
    receipt_id: Mapped[int] = mapped_column(primary_key=True)
    slot_time: Mapped[float] = mapped_column(Float)
    total_price: Mapped[DECIMAL] = mapped_column(DECIMAL(10, 2))
    group_id: Mapped[int] = mapped_column(Integer, ForeignKey('groups.group_id', ondelete='CASCADE'))
    payment_card: Mapped[int]  # Last four digits of the payment card
    locked_by: Mapped[bool] = mapped_column(Integer)          # User ID of whoever is opening the receipt
    lock_timestamp: Mapped[DECIMAL] = mapped_column(DECIMAL)  # Timestamp of locks
    
    # ----- Relationships -----
    # Bi-directional relationship - plural 'items' as a receipt can contain multiple items
    items: Mapped[List[Item]] = relationship("Item", back_populates="receipt", cascade="all, delete-orphan")
    group: Mapped[Group] = relationship("Group", back_populates="receipts")
    
    # ----- Methods -----
    def __repr__(self):
        return f"Receipt ID: {self.receipt_id!r}, delivered at {self.slot_time!r}, paid GBP{self.price!r} with card no. {self.payment_card!r}"
    

class Item(Base):
    
    __tablename__ = "items"
    
    # ----- Columns -----
    item_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))
    receipt_id: Mapped[int] = mapped_column(ForeignKey('receipts.receipt_id'))
    quantity: Mapped[Optional[int]] = mapped_column(Integer)
    weight: Mapped[Optional[float]] = mapped_column(Float)
    price: Mapped[DECIMAL] = mapped_column(DECIMAL(10, 2))
    
    # ----- Relationships -----
    # One-to-many - an item only belong to one receipt
    receipt: Mapped[User] = relationship("Receipt", back_populates="items")
    # Many-to-many - An item can belong to multiple users
    users: Mapped[User] = relationship("User", secondary=user_items, back_populates="items")

    
if __name__ == "__main__":
    # Create an engine as a means to connect
    engine = create_engine(f"sqlite:///{DATABASE_FILE}")

    # Create the datatables
    Base.metadata.create_all(engine)
    
    # Setup data to be inserted or modified
    group1 = Group(group_name="Honeysuckle", description="Sleeping")
    group2 = Group(group_name="Broadlands", description="The rich house")
    user1 = User(username="Gai Zhe")
    user2 = User(username="Kelly")
    
    group1.users.append(user1)
    group2.users.append(user1)
    group2.users.append(user2)

    # Begin a session
    Session = sessionmaker(bind=engine)
    session = Session()
    session.add(group1)
    session.add(group2)
    

    # Commit and close the session
    session.commit()
    session.close()

