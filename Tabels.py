import os
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, Table, Date
from sqlalchemy.orm import relationship, declarative_base, sessionmaker

Base = declarative_base()

# טבלת עזר לניהול הקשר "רבים לרבים"
soldier_roles = Table('soldier_roles', Base.metadata,
                      Column('soldier_id', Integer, ForeignKey('soldiers.id')),
                      Column('role_id', Integer, ForeignKey('roles.id'))
                      )

class Role(Base):
    __tablename__ = 'roles'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

class Soldier(Base):
    __tablename__ = 'soldiers'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    # שינוי כאן: מ-Integer ל-String כדי לתמוך בשמות מחלקות
    platoon_number = Column(String)
    is_active = Column(Boolean, default=True)

    roles = relationship('Role', secondary=soldier_roles, backref='soldiers')

class PlatoonRequirement(Base):
    __tablename__ = 'requirements'
    id = Column(Integer, primary_key=True)
    # שינוי כאן: מ-Integer ל-String כדי לתמוך בשמות מחלקות
    platoon_number = Column(String)
    role_id = Column(Integer, ForeignKey('roles.id'))
    min_required = Column(Integer, default=1)

# --- הטבלה החדשה: יציאות הביתה ואילוצים ---
class LeaveRecord(Base):
    __tablename__ = 'leave_records'
    id = Column(Integer, primary_key=True)
    soldier_id = Column(Integer, ForeignKey('soldiers.id'))
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    reason = Column(String)
    is_mandatory = Column(Boolean, default=False)

    soldier = relationship("Soldier", backref="leaves")

# יצירת מסד הנתונים עם נתיב מוחלט
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, 'platoon_app.db')

engine = create_engine(f'sqlite:///{db_path}')
Base.metadata.create_all(engine)

print("התשתית המעודכנת הוקמה! (תומך בשמות מחלקות)")