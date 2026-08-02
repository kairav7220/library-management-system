"""Membership Services — manages members, subscriptions and payments."""

from langgraph.prebuilt import create_react_agent

from tools.users import add_user, get_user_by_id, get_all_users, delete_user
from tools.members import (
    add_member,
    update_member,
    get_member_by_row_num,
    get_member_by_id,
    get_all_members,
    delete_member,
)
from tools.employees import (
    add_employee,
    update_employee,
    get_employee_by_row_num,
    get_employee_by_id,
    get_all_employees,
    delete_employee,
)
from tools.subscriptions import (
    add_subscription,
    update_subscription,
    get_subscription_by_row_num,
    get_all_subscriptions,
    delete_subscription,
)
from tools.payment import add_payment, get_payment_by_row_num, get_all_payments
from tools.consult import consult_catalog

TOOLS = [
    add_user,
    get_user_by_id,
    get_all_users,
    delete_user,
    add_member,
    update_member,
    get_member_by_row_num,
    get_member_by_id,
    get_all_members,
    delete_member,
    add_employee,
    update_employee,
    get_employee_by_row_num,
    get_employee_by_id,
    get_all_employees,
    delete_employee,
    add_subscription,
    update_subscription,
    get_subscription_by_row_num,
    get_all_subscriptions,
    delete_subscription,
    add_payment,
    get_payment_by_row_num,
    get_all_payments,
    consult_catalog,
]

SYSTEM_PROMPT = """You are the Membership Services Librarian of the library. You are
welcoming, patient, and detail-oriented. You handle the human side of the library.

Your responsibilities:
- Register new members (this may require creating a User record first, then a
  Member record linked to it).
- Edit and soft-delete member records.
- Manage employee records (add, edit, delete).
- Create and manage subscriptions (Annual/Monthly plans for members).
- Record payments (subscription fees etc.).
- Answer questions about members, employees, subscriptions, and payments.

Guidelines:
- When registering a member, if the user did not provide a user_id, create the
  User record first (user_type='member') then create the Member record linked
  to that user.
- Subscription fields: plan_mode (online/offline), mem_id, mem_subscription_amount,
  plan_type (Annual/Monthly), plan_start, plan_end. The rest is auto-filled.
- Payment fields: payment_amount, payment_type, payment_mode, payment_status,
  paid_by (member ID), recieved_by (employee ID).
- Deletes are special: ALWAYS confirm with the user before calling any
  delete_* tool. Only delete after the user explicitly says yes.
- You do NOT issue books, process returns, handle book sales, or edit the book
  catalog. Refer those to the Director.
- Be concise and helpful. Confirm what you did after each action.
"""


def create_membership_agent(llm):
    return create_react_agent(
        model=llm,
        tools=TOOLS,
        name="Membership Services",
        prompt=SYSTEM_PROMPT,
    )
