"""Merge migration heads

Revision ID: 51db40435d94
Revises: 406ad6bf784d, f2694d5d69bb
Create Date: 2026-09-15 13:49:13.273902

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '51db40435d94'
down_revision = ('406ad6bf784d', 'f2694d5d69bb')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
