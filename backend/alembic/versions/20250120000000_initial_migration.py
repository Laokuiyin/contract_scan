"""Initial migration

Revision ID: 20250120000000
Revises:
Create Date: 2025-01-20 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20250120000000'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create contracts table
    op.create_table(
        'contracts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('contract_number', sa.String(100), nullable=False, unique=True),
        sa.Column('contract_type', sa.Enum('purchase', 'sales', 'lease', name='contracttype'), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('ocr_text_path', sa.String(500)),
        sa.Column('status', sa.Enum('pending_ocr', 'ocr_processing', 'pending_ai', 'ai_processing', 'pending_review', 'completed', name='contractstatus'), nullable=False, server_default='pending_ocr'),
        sa.Column('upload_time', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('created_by', sa.String(100)),
        sa.Column('total_amount', sa.Numeric(15, 2)),
        sa.Column('subject_matter', sa.Text),
        sa.Column('sign_date', sa.DateTime),
        sa.Column('effective_date', sa.DateTime),
        sa.Column('expire_date', sa.DateTime),
        sa.Column('confidence_score', sa.Float),
        sa.Column('requires_review', sa.Boolean(), server_default='true'),
    )
    op.create_index('ix_contracts_contract_number', 'contracts', ['contract_number'], unique=True)
    op.create_index('ix_contracts_status', 'contracts', ['status'])
    op.create_index('ix_contract_type_date', 'contracts', ['contract_type', 'sign_date'])
    op.create_index('ix_confidence_score', 'contracts', ['confidence_score'])

    # Create contract_parties table
    op.create_table(
        'contract_parties',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('contract_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('party_type', sa.Enum('party_a', 'party_b', name='partytype'), nullable=False),
        sa.Column('party_name', sa.String(500), nullable=False),
        sa.Column('party_type_detail', sa.String(50)),
        sa.Column('tax_number', sa.String(50)),
        sa.Column('legal_representative', sa.String(100)),
        sa.Column('address', sa.Text),
        sa.Column('contact_info', sa.Text),
        sa.Column('confidence_score', sa.Float),
        sa.ForeignKeyConstraint(['contract_id'], ['contracts.id'], ),
    )
    op.create_index('ix_contract_parties_contract_id', 'contract_parties', ['contract_id'])

    # Create ai_extraction_results table
    op.create_table(
        'ai_extraction_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('contract_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('field_name', sa.String(100), nullable=False),
        sa.Column('raw_value', sa.Text),
        sa.Column('reasoning', sa.Text),
        sa.Column('confidence_score', sa.Float),
        sa.Column('model_version', sa.String(50)),
        sa.Column('prompt_template', sa.String(100)),
        sa.Column('extract_time', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['contract_id'], ['contracts.id'], ),
    )
    op.create_index('ix_ai_extraction_results_contract_id', 'ai_extraction_results', ['contract_id'])

    # Create review_records table
    op.create_table(
        'review_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('contract_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('field_name', sa.String(100), nullable=False),
        sa.Column('ai_value', sa.Text),
        sa.Column('human_value', sa.Text),
        sa.Column('reviewer', sa.String(100), nullable=False),
        sa.Column('review_time', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('is_correct', sa.Boolean()),
        sa.Column('notes', sa.Text),
        sa.ForeignKeyConstraint(['contract_id'], ['contracts.id'], ),
    )
    op.create_index('ix_review_records_contract_id', 'review_records', ['contract_id'])


def downgrade() -> None:
    op.drop_index('ix_review_records_contract_id', table_name='review_records')
    op.drop_table('review_records')

    op.drop_index('ix_ai_extraction_results_contract_id', table_name='ai_extraction_results')
    op.drop_table('ai_extraction_results')

    op.drop_index('ix_contract_parties_contract_id', table_name='contract_parties')
    op.drop_table('contract_parties')

    op.drop_index('ix_confidence_score', table_name='contracts')
    op.drop_index('ix_contract_type_date', table_name='contracts')
    op.drop_index('ix_contracts_status', table_name='contracts')
    op.drop_index('ix_contracts_contract_number', table_name='contracts')
    op.drop_table('contracts')

    op.execute('DROP TYPE IF EXISTS contracttype')
    op.execute('DROP TYPE IF EXISTS contractstatus')
    op.execute('DROP TYPE IF EXISTS partytype')
