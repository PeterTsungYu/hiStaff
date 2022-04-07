"""add more leaves

Revision ID: ff7f4a181833
Revises: 46acb87f4e02
Create Date: 2022-04-06 20:35:07.319409

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ff7f4a181833'
down_revision = '46acb87f4e02'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('staffs_table', schema=None) as batch_op:
        batch_op.add_column(sa.Column('Personal_Leave', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('Sick_Leave', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('Business_Leave', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('Deffered_Leave', sa.Float(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('staffs_table', schema=None) as batch_op:
        batch_op.drop_column('Deffered_Leave')
        batch_op.drop_column('Business_Leave')
        batch_op.drop_column('Sick_Leave')
        batch_op.drop_column('Personal_Leave')

    # ### end Alembic commands ###