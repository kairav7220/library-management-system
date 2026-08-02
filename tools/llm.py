from langchain_mistralai import ChatMistralAI
from langchain_core.messages import BaseMessage
from dotenv import load_dotenv
import os

load_dotenv()


def get_llm() -> ChatMistralAI:
    return ChatMistralAI(
        api_key=os.environ.get("MISTRAL_API_KEY"),
        model="open-mistral-7b",
        temperature=0.1,
    )


def get_tools():
    from tools.book import (
        add_book,
        update_book,
        get_book_by_row_num,
        get_all_books,
        delete_book,
    )
    from tools.book_cat import (
        add_category,
        update_category,
        get_category_by_row_num,
        get_all_categories,
        get_books_by_category,
        delete_category,
    )
    from tools.book_genre import (
        add_book_genre,
        update_book_genre,
        get_book_genre_by_row_num,
        get_all_book_genres,
        delete_book_genre,
    )
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
    from tools.book_issue import (
        book_issue,
        book_return,
        get_issue_by_row_num,
        get_all_issues,
    )
    from tools.book_sell import book_sell, update_book_sell, get_all_book_sells
    from tools.rag_tools import search_books_rag, reindex_books
    from tools.consult import consult_membership, consult_catalog, consult_circulation

    return [
        # Catalog Librarian
        add_book,
        update_book,
        get_book_by_row_num,
        get_all_books,
        delete_book,
        add_category,
        update_category,
        get_category_by_row_num,
        get_all_categories,
        get_books_by_category,
        delete_category,
        add_book_genre,
        update_book_genre,
        get_book_genre_by_row_num,
        get_all_book_genres,
        delete_book_genre,
        # Circulation Librarian
        book_issue,
        book_return,
        get_issue_by_row_num,
        get_all_issues,
        book_sell,
        update_book_sell,
        get_all_book_sells,
        # Membership Services
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
        # Reference Librarian (RAG)
        search_books_rag,
        reindex_books,
        # Cross-agent (peer-to-peer)
        consult_membership,
        consult_catalog,
        consult_circulation,
    ]
