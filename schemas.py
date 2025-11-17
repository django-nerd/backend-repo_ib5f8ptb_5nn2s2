"""
Database Schemas for Éclat Dining – Luxury Veg Gourmet Restaurant

Each Pydantic model below represents a MongoDB collection. The collection name
is the lowercase of the class name (e.g., MenuItem -> "menuitem").

These schemas are used for validation in API endpoints and by the built-in
Flames database viewer via the /schema endpoint.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime

# Core content
class MenuItem(BaseModel):
    name: str = Field(..., description="Dish name")
    description: Optional[str] = Field(None, description="Short description")
    price: float = Field(..., ge=0, description="Price in local currency")
    category: str = Field(..., description="Category: Pizzas | Pastas | Starters | Desserts | Drinks")
    image_url: Optional[str] = Field(None, description="Public image URL")
    featured: bool = Field(False, description="Show as featured")
    vegetarian: bool = Field(True, description="Veg-only flag")

class Special(BaseModel):
    title: str
    description: Optional[str] = None
    discount_percent: Optional[int] = Field(None, ge=0, le=100)
    valid_until: Optional[datetime] = None
    hero_image_url: Optional[str] = None
    cta_text: Optional[str] = "Reserve Now"
    active: bool = True

class GalleryImage(BaseModel):
    url: str
    caption: Optional[str] = None
    order: Optional[int] = 0

class Testimonial(BaseModel):
    name: str
    rating: int = Field(5, ge=1, le=5)
    comment: str
    avatar_url: Optional[str] = None
    featured: bool = False

# Interactions
class ContactMessage(BaseModel):
    name: str
    email: EmailStr
    message: str

class Reservation(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    date: str = Field(..., description="YYYY-MM-DD")
    time: str = Field(..., description="HH:MM")
    guests: int = Field(..., ge=1, le=20)
    notes: Optional[str] = None
    paid: bool = False
    payment_reference: Optional[str] = None

# Admin & telemetry
class AdminUser(BaseModel):
    email: EmailStr
    password_hash: str
    role: str = Field("admin", description="admin | editor | viewer")
    active: bool = True

class AnalyticsEvent(BaseModel):
    type: str = Field(..., description="page_view | reservation_submit | contact_submit | conversion | custom")
    path: Optional[str] = None
    metadata: Optional[dict] = None
    user_agent: Optional[str] = None
    ip: Optional[str] = None
