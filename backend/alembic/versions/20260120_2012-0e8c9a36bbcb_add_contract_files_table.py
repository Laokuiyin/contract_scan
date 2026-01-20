"""add_contract_files_table

Revision ID: 0e8c9a36bbcb
Revises: 20250120000000
Create Date: 2026-01-20 20:12:05.270491

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0e8c9a36bbcb'
down_revision: Union[str, None] = '20250120000000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create contract_files table
    op.create_table(
        'contract_files',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('contract_id', sa.UUID(), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('upload_time', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['contract_id'], ['contracts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_contract_files_contract_id'), 'contract_files', ['contract_id'], unique=False)


def downgrade() -> None:
    # Drop contract_files table
    op.drop_index(op.f('ix_contract_files_contract_id'), table_name='contract_files')
    op.drop_table('contract_files')
