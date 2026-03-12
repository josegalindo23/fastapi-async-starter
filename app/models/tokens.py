"""
app/models/tokens.py

RefreshToken model — stores issued refresh tokens in the database.

Why store refresh tokens in DB?
- Enables true logout (token revocation)
- Allows "logout from all devices"
- Prevents refresh token reuse after rotation
"""

from datetime import datetime, timezone
from sqlalchemy import Boolean, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    # ── Primary Key ──────────────────────────────
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # ── Token data ───────────────────────────────
    # Store the full JWT — lets us look it up on refresh requests
    token: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)

    # jti from the JWT payload — used for fast revocation checks
    jti: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)

    # ── Status ───────────────────────────────────
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # ── Timestamps ───────────────────────────────
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Foreign Key ──────────────────────────────
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # ── Relationship ─────────────────────────────
    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")

    # ── Composite index for common query: user's active tokens ──
    __table_args__ = (
        Index("ix_refresh_tokens_user_id_is_revoked", "user_id", "is_revoked"),
    )

    @property
    def is_expired(self) -> bool:
        """
        Compare expiry against current UTC time.
        SQLite returns naive datetimes — normalize both sides to UTC before comparing.
        """
        expires = self.expires_at
        if expires.tzinfo is None:
            # SQLite strips tzinfo on read — the stored value is UTC, restore it
            expires = expires.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) > expires

    @property
    def is_valid(self) -> bool:
        """Token is usable only if not revoked and not expired."""
        return not self.is_revoked and not self.is_expired

    def revoke(self) -> None:
        """Mark this token as revoked."""
        self.is_revoked = True
        self.revoked_at = datetime.now(timezone.utc)

    def __repr__(self) -> str:
        return (
            f"<RefreshToken(id={self.id}, user_id={self.user_id}, "
            f"revoked={self.is_revoked}, expires={self.expires_at})>"
        )