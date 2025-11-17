"""initial models

Revision ID: 001
Revises:
Create Date: 2025-11-17 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create agents table
    op.create_table('agents',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('role', sa.Enum('PRODUCER', 'AUDITOR', 'LOGISTICS', 'RETAILER', name='roletype'), nullable=False),
        sa.Column('public_key', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create schemas table
    op.create_table('schemas',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('deadline_hours', sa.Integer(), nullable=False),
        sa.Column('required_role', sa.Enum('PRODUCER', 'AUDITOR', 'LOGISTICS', 'RETAILER', name='roletype'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create product_batches table
    op.create_table('product_batches',
        sa.Column('batch_id', sa.String(), nullable=False),
        sa.Column('product_name', sa.String(), nullable=False),
        sa.Column('current_custodian_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['current_custodian_id'], ['agents.id'], ),
        sa.PrimaryKeyConstraint('batch_id')
    )

    # Create assertions table
    op.create_table('assertions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('batch_id', sa.String(), nullable=False),
        sa.Column('agent_id', sa.String(), nullable=False),
        sa.Column('schema_id', sa.String(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('location_gps', sa.String(), nullable=True),
        sa.Column('content_data', sa.JSON(), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'VERIFIED', 'REJECTED', 'TIMED_OUT', 'ENACTED', name='claimstatus'), nullable=True),
        sa.Column('signature', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
        sa.ForeignKeyConstraint(['batch_id'], ['product_batches.batch_id'], ),
        sa.ForeignKeyConstraint(['schema_id'], ['schemas.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create index on assertions for fast queries
    op.create_index('ix_assertions_batch_status_timestamp', 'assertions', ['batch_id', 'status', 'timestamp'])

    # Create evaluations table
    op.create_table('evaluations',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('assertion_id', sa.String(), nullable=False),
        sa.Column('agent_id', sa.String(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('result', sa.Boolean(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('signature', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
        sa.ForeignKeyConstraint(['assertion_id'], ['assertions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create enactments table
    op.create_table('enactments',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('assertion_id', sa.String(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('blockchain_hash', sa.String(), nullable=True),
        sa.Column('enacted_by', sa.String(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['assertion_id'], ['assertions.id'], ),
        sa.ForeignKeyConstraint(['enacted_by'], ['agents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create audit_log table
    op.create_table('audit_log',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('actor_id', sa.String(), nullable=True),
        sa.Column('action', sa.String(), nullable=True),
        sa.Column('payload', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('audit_log')
    op.drop_table('enactments')
    op.drop_table('evaluations')
    op.drop_index('ix_assertions_batch_status_timestamp', table_name='assertions')
    op.drop_table('assertions')
    op.drop_table('product_batches')
    op.drop_table('schemas')
    op.drop_table('agents')
    op.execute('DROP TYPE roletype')
    op.execute('DROP TYPE claimstatus')
