"""0_create tables

Revision ID: 65de66039a88
Revises: 
Create Date: 2022-07-13 16:13:48.084413

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '65de66039a88'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('staffs_table',
    sa.Column('uuid', sa.String(), nullable=False),
    sa.Column('staff_name', sa.String(), nullable=False),
    sa.Column('Official_Leave', sa.Float(), nullable=True),
    sa.Column('Personal_Leave', sa.Float(), nullable=True),
    sa.Column('Sick_Leave', sa.Float(), nullable=True),
    sa.Column('Business_Leave', sa.Float(), nullable=True),
    sa.Column('Deferred_Leave', sa.Float(), nullable=True),
    sa.Column('Annual_Leave', sa.Float(), nullable=True),
    sa.Column('Funeral_Leave', sa.Float(), nullable=True),
    sa.Column('Menstruation_Leave', sa.Float(), nullable=True),
    sa.Column('Marital_Leave', sa.Float(), nullable=True),
    sa.Column('Maternity_Leave', sa.Float(), nullable=True),
    sa.Column('Paternity_Leave', sa.Float(), nullable=True),
    sa.PrimaryKeyConstraint('uuid')
    )
    op.create_table('users_table',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('nick_name', sa.String(), nullable=True),
    sa.Column('image_url', sa.String(length=256), nullable=True),
    sa.Column('created_time', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('checkin_table',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('staff_name', sa.String(), nullable=True),
    sa.Column('created_time', sa.DateTime(), nullable=True),
    sa.Column('check_place', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['staff_name'], ['staffs_table.staff_name'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('checkout_table',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('staff_name', sa.String(), nullable=True),
    sa.Column('created_time', sa.DateTime(), nullable=True),
    sa.Column('check_place', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['staff_name'], ['staffs_table.staff_name'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('leaves_table',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('staff_name', sa.String(), nullable=False),
    sa.Column('type', sa.String(), nullable=False),
    sa.Column('start', sa.DateTime(), nullable=True),
    sa.Column('end', sa.DateTime(), nullable=True),
    sa.Column('reserved', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['staff_name'], ['staffs_table.staff_name'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('leaves_table')
    op.drop_table('checkout_table')
    op.drop_table('checkin_table')
    op.drop_table('users_table')
    op.drop_table('staffs_table')
    # ### end Alembic commands ###
