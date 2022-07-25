"""4_revsed col as string type

Revision ID: ecaa291a48e7
Revises: e2023adb2234
Create Date: 2022-07-20 11:00:08.977093

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ecaa291a48e7'
down_revision = 'e2023adb2234'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('checkin_table', schema=None) as batch_op:
        batch_op.alter_column('revised',
               existing_type=sa.BOOLEAN(),
               type_=sa.String(),
               existing_nullable=True)

    with op.batch_alter_table('checkout_table', schema=None) as batch_op:
        batch_op.alter_column('revised',
               existing_type=sa.BOOLEAN(),
               type_=sa.String(),
               existing_nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('checkout_table', schema=None) as batch_op:
        batch_op.alter_column('revised',
               existing_type=sa.String(),
               type_=sa.BOOLEAN(),
               existing_nullable=True)

    with op.batch_alter_table('checkin_table', schema=None) as batch_op:
        batch_op.alter_column('revised',
               existing_type=sa.String(),
               type_=sa.BOOLEAN(),
               existing_nullable=True)

    # ### end Alembic commands ###
