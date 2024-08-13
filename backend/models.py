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
    Column('item_id', Integer, ForeignKey('items.item_id'), primary_key=True),
    Column('weight', float, nullable=True),  # Optional for precise splitting
    Column('quantity', float, nullable=True)
)


# ----- Data Tables -----
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
    group_name: Mapped[str] = mapped_column(String(10))  # VARCHAR(20)
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
        result = session.query(cls).filter_by(group_name=group_name).first()
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
    username: Mapped[str] = mapped_column(String(10))
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
        result = session.query(cls).filter_by(username=username).first()
        return result is not None
    
    @classmethod
    def get_usernames_in_group(cls, session: Session, group_id: int) -> Tuple[str]:
        """Return a tuple of usernames within a specified group"""
        # NOTE: '.c' is a shorthand for columns
        usernames = session.query(User.username).join(user_groups).filter(user_groups.c.group_id == group_id).all()
        return usernames
    
    @classmethod
    def add_items_to_user(session: Session, item_id: int, user_id: int):
        """Add an item

        Args:
            session (Session): A SQLAlchemy Session object.
            item_id (int): 
            user_id (int): 
        """
        
        user = session.query(User).filter_by(user_id=user_id).one_or_none()
        item = session.query(Item).filter_by(item_id=item_id).one_or_none()

        if user and item:  # Must be existing user and item
            user.items.append(item)  # Update association table 'user_items'
    
    def __repr__(self) -> str:
        return f"User"


class Receipt(Base):
    
    __tablename__ = "receipts"
    
    receipt_id: Mapped[int] = mapped_column(primary_key=True)
    slot_time: Mapped[float] = mapped_column(Float)
    total_price: Mapped[DECIMAL] = mapped_column(DECIMAL(10, 2))
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
    name: Mapped[str] = mapped_column(String(255))
    receipt_id: Mapped[int] = mapped_column(ForeignKey('receipts.receipt_id'))
    quantity: Mapped[Optional[int]] = mapped_column(Integer)
    weight: Mapped[Optional[float]] = mapped_column(Float)
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

