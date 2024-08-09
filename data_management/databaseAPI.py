"""
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


# ----- Association Tables ----- 
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
    Column('item_id', Integer, ForeignKey('items.item_id'), primary_key=True)
)


# ----- Data Tables -----
class Group(Base):
    """
    SQLALchemy Database entry object.

    Args:
        id (int): Group ID as the primary key. Autoincremented.
        name (VARCHAR(20)): Name of the group
        description(VARCHAR(50)): Description of the group, such as rules.
    """
    
    __tablename__ = "groups"
    
    # ----- Columns -----
    group_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(10))  # VARCHAR(20)
    description: Mapped[str] = mapped_column(String(50))  # VARCHAR(50)
    
    
    # ----- Relationships -----
    # A group can have multiple users
    users: Mapped[List["User"]] = relationship("User", secondary=user_groups, back_populates="groups")
    # A group can have multiple receipts
    receipts: Mapped[List["Receipt"]] = relationship("Receipt", back_populates="group")
    
    @classmethod
    def get_all_group_names(cls, session: Session):
        """Return a list of all group names."""
        return session.query(cls.name).scalars().all()
    
    @classmethod
    def group_exists(cls, session: Session, group_name: str) -> bool:
        """Check if a group exists within the 'groups' data table."""
        result = session.query(cls).filter_by(name=group_name).first()
        return result is not None
    
    # @classmethod
    # def add_user_to_group(cls, username: str, group_name:int, session: Session) -> bool:
    #     """Add a user to a group."""
    #     # # Verify that the user and group already exists in the 'users' and 'groups' table
    #     # if not User.user_exists(session, username) and cls.group_exists(session, group_name):
    #     #     print("User or group does not exist.")
    #     #     return None
        
    #     # # Add new record to user_groups
        
    @classmethod
    def add_receipt_to_group(cls, session: Session, receipt: Receipt, group: Group) -> bool:
        """Add a receipt to a group

        Args:
            receipt (Receipt): _description_
            group (Group): _description_

        Returns:
            bool: Return true if receipt is successfully added
        """
    
    def __repr__(self) -> str:
        return f"Group(id={self.group_id!r}, name = {self.name!r}, description = {self.description!r})"
    

class User(Base):
    
    __tablename__ = "users"
    
    # Columns
    # -------------------------------------------------------------------------
    user_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(10))
    # password_hashed: Mapped[str] = mapped_column(String(50))
    
    # Relationships
    # -------------------------------------------------------------------------
    # A user can join multiple groups
    groups: Mapped[List[Group]] = relationship("Group", secondary=user_groups, back_populates="users")
    # A user can have multiple items
    items: Mapped[List[Item]] = relationship("Item", secondary=user_items, back_populates="users")
    
    # Methods
    # -------------------------------------------------------------------------
    @classmethod
    def get_all_users(cls, session: Session) -> Tuple["User"]:
        """Return all users in the database in the form of a User object, useful for accessing
        the attributes of users"""
        return session.query(cls).all()
    
    @classmethod
    def user_exists(cls, session: Session, username: str) -> bool:
        """Given a username, return True if user exists and False otherwise."""
        result = session.query(cls).filter_by(name=username).first()
        return result is not None
    
    @classmethod
    def get_usernames_in_group(cls, session: Session, group_id: int) -> Tuple[str]:
        """Return a tuple of usernames within a specified group"""
        # NOTE: '.c' is a shorthand for columns
        usernames = session.query(User.name).join(user_groups).filter(user_groups.c.group_id == group_id).all()
        return usernames
    
    def __repr__(self) -> str:
        return f"User"


class Receipt(Base):
    
    __tablename__ = "receipts"
    
    receipt_id: Mapped[int] = mapped_column(primary_key=True)
    slot_time: Mapped[float] = mapped_column(Float)
    price: Mapped[DECIMAL] = mapped_column(DECIMAL(10, 2))
    group_id: Mapped[int] = mapped_column(Integer, ForeignKey('groups.group_id', ondelete='CASCADE'))
    payment_card: Mapped[int]  # Last four digits of the payment card
    
    # ----- Relationships -----
    # Bi-directional relationship - plural 'items' as a receipt can contain multiple items
    items: Mapped[List[Item]] = relationship("Item", back_populates="receipt", cascade="all, delete-orphan")
    group: Mapped[Group] = relationship("Group", back_populates="receipts")
    
    # ----- Methods -----
    @classmethod
    def get_all_receipts(cls, session: Session) -> list[Receipt]:
        """Get A LIST of all receipts as a Receipt object

        Args:
            session (Session): The SQLAlchemy session object.

        Returns:
            _type_: _description_
        """
        return session.query(cls).all()
    
    @classmethod
    def get_all_receipt_dates(cls, session: Session) -> list[float]:
        """Get a list of all receipt dates in timestamps.

        Args:
            session (Session): The SQLAlchemy session object

        Returns:
            list[float]: A list of all receipt dates returned as timestamps.
        """
        return session.query(cls.slot_time).all()
    
    @classmethod
    def delete_receipt_by_id(cls, session: Session, receipt_id: int) -> bool:
        """Delete a receipt by its id.

        Args:
            session (Session): The SQLAlchemy session object.
            receipt_id (int): The ID of the receipt to delete.

        Returns:
            bool: True if the receipt was deleted, False if not found
        """
        receipt = session.query(cls).filter_by(id=receipt_id).one_or_none()
        if receipt:
            session.delete(receipt)
            session.commit()
            return True
        return False
    
    def __repr__(self):
        return f"Receipt ID: {self.receipt_id!r}, delivered at {self.slot_time!r}, paid GBP{self.price!r} with card no. {self.payment_card!r}"
    

class Item(Base):
    
    __tablename__ = "items"
    
    # Columns
    # -------------------------------------------------------------------------
    item_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    receipt_id: Mapped[int] = mapped_column(ForeignKey('receipts.receipt_id'))
    quantity: Mapped[Optional[int]] = mapped_column(Integer)
    weight: Mapped[Optional[float]] = mapped_column(Float)
    name: Mapped[str] = mapped_column(String(255))
    price: Mapped[DECIMAL] = mapped_column(DECIMAL(10, 2))
    
    # Relationships
    # -------------------------------------------------------------------------
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
    user1 = User(user_id="32248873", name="Gai Zhe")
    user2 = User(user_id="38329329", name="Kelly")
    user3 = User(user_id="23454664", name="Rick")
    group1 = Group(name="Honeysuckle", description="Sleeping Rick")
    group2 = Group(name="Broadlands", description="The rich house")
    # Parent receipt is linked to child item. Adding 'receipt1' will add child items as well.
    receipt1 = Receipt(receipt_id=1234, slot_time=323211, price=78.876, payment_card=2341, group_id=1)
    receipt2 = Receipt(receipt_id=2325, slot_time=424443, price=23.874, payment_card=9891, group_id=2)
    item1 = Item(quantity=1, name="Tenderstem", price=0.52, receipt=receipt2)
    item2 = Item(quantity=2, name="Broccoli", price=0.52, receipt=receipt2)
    item3 = Item(weight=0.86, name="Mango", price=2, receipt=receipt2)

    user1.groups.append(group1)
    user1.groups.append(group2)
    user2.groups.append(group2)
    user3.groups.append(group1)

    # Begin a session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Add the database entries with their associated data (e.g., user and their groups)
    session.add(user1)
    session.add(user2)
    session.add(user3)
    # session.add(group1)
    # session.add(group2)
    session.add(receipt1)
    session.add(receipt2) 

    # Query to display the results
    users = session.query(User).all()
    groups = session.query(Group).all()

    print("Users:")
    for user in users:
        print(user)
        print(f"  Groups: {[group.name for group in user.groups]}")

    print("Groups:")
    for group in groups:
        print(group)
        print(f"  Users: {[user.name for user in group.users]}")
        
    print("Who is in Honeysuckle?")
    for name in User.get_usernames_in_group(session, 1):
        print(name)
        
    print("Who is in Honeysuckle?")
    for name in User.get_usernames_in_group(session, 1):
        print(name)
    
    print("Fetching all receipts")
    result = Receipt.get_all_receipts(session)
    print(f'result is of type {type(result)}')
    for rec in result:
        print(rec)

    # Commit and close the session
    session.commit()
    session.close()

