from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

class TimestampMixin:
    last_edited: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

class AchievementIndex(TimestampMixin, db.Model):
    __tablename__ = "achievements_index"
    achievement_id = db.Column(db.Integer, primary_key=True)
    exists_us = db.Column(db.Boolean, default=False)
    exists_eu = db.Column(db.Boolean, default=False)
    exists_tw = db.Column(db.Boolean, default=False)
    exists_kr = db.Column(db.Boolean, default=False)
    criteria_id = db.Column(db.Integer, db.ForeignKey("criteria.criteria_id"), nullable=True)

    criteria = db.relationship("Criteria", back_populates="achievement")


class AchievementString(TimestampMixin, db.Model):
    __tablename__ = "achievement_strings"
    achievement_id = db.Column(db.Integer, db.ForeignKey("achievements_index.achievement_id"), primary_key=True)
    locale = db.Column(db.String(8), primary_key=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String)
    reward = db.Column(db.String)

    achievement = db.relationship("AchievementIndex", backref="strings")


class Criteria(TimestampMixin, db.Model):
    __tablename__ = "criteria"
    criteria_id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50))
    achievement_id = db.Column(db.Integer, db.ForeignKey("achievements_index.achievement_id"))
    parent_achievement_id = db.Column(db.Integer, db.ForeignKey("achievements_index.achievement_id"), nullable=True)

    achievement = db.relationship("AchievementIndex", foreign_keys=[achievement_id], back_populates="criteria")
    parent_achievement = db.relationship("AchievementIndex", foreign_keys=[parent_achievement_id], viewonly=True)
    details = db.relationship("CriteriaDetail", back_populates="criteria")


class CriteriaDetail(TimestampMixin, db.Model):
    __tablename__ = "criteria_details"
    criteria_id = db.Column(db.Integer, db.ForeignKey("criteria.criteria_id"), primary_key=True)
    locale = db.Column(db.String(8), primary_key=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String)

    criteria = db.relationship("Criteria", back_populates="details")


class Realm(TimestampMixin, db.Model):
    __tablename__ = "realms"
    id = db.Column(db.Integer, primary_key=True)
    region = db.Column(db.String(2), primary_key=True)
    name = db.Column(db.String, nullable=False)
    slug = db.Column(db.String, nullable=False)
