from .db import get_db
from datetime import datetime


def get_user_by_id(user_id):
    """
    Retrieve user details by ID.

    Args:
        user_id: The user's ID

    Returns:
        A dict with keys: name, email, member_since
        member_since is formatted as "Month YYYY" (e.g. "January 2026")
        Returns None if user not found
    """
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name, email, created_at FROM users WHERE id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None

        # Parse created_at and format as "Month YYYY"
        created_at_str = row[2]
        created_at = datetime.strptime(created_at_str, "%Y-%m-%d %H:%M:%S")
        member_since = created_at.strftime("%B %Y")

        return {
            'name': row[0],
            'email': row[1],
            'member_since': member_since
        }
    finally:
        conn.close()


def get_recent_transactions(user_id, limit=10):
    """
    Retrieve recent transactions for a user, ordered by date (newest first).

    Args:
        user_id: The user's ID
        limit: Maximum number of transactions to return (default: 10)

    Returns:
        A list of dicts with keys: date, description, category, amount
        Empty list if the user has no expenses
    """
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, date, description, category, amount FROM expenses WHERE user_id = ? ORDER BY date DESC LIMIT ?",
            (user_id, limit)
        )
        rows = cursor.fetchall()

        # Convert rows to list of dicts
        transactions = []
        if rows:
            for row in rows:
                transactions.append({
                    'date': row[1],
                    'description': row[2],
                    'category': row[3],
                    'amount': row[4]
                })

        return transactions
    finally:
        conn.close()


def get_summary_stats(user_id):
    """
    Retrieve summary statistics for a user's expenses.

    Args:
        user_id: The user's ID

    Returns:
        A dict with keys:
            - total_spent (float): Sum of all expenses; 0.0 if no expenses
            - transaction_count (int): Count of all expenses; 0 if no expenses
            - top_category (str): Category with highest sum; "—" if no expenses
    """
    conn = get_db()
    try:
        cursor = conn.cursor()

        # Get total spent
        cursor.execute(
            "SELECT SUM(amount) FROM expenses WHERE user_id = ?",
            (user_id,)
        )
        total_spent = cursor.fetchone()[0] or 0.0

        # Get transaction count
        cursor.execute(
            "SELECT COUNT(*) FROM expenses WHERE user_id = ?",
            (user_id,)
        )
        transaction_count = cursor.fetchone()[0] or 0

        # Get top category
        cursor.execute(
            "SELECT category FROM expenses WHERE user_id = ? GROUP BY category ORDER BY SUM(amount) DESC LIMIT 1",
            (user_id,)
        )
        top_category_row = cursor.fetchone()
        top_category = top_category_row[0] if top_category_row else "—"

        return {
            'total_spent': total_spent,
            'transaction_count': transaction_count,
            'top_category': top_category
        }
    finally:
        conn.close()


def get_category_breakdown(user_id):
    """
    Retrieve category breakdown for a user's expenses.

    Args:
        user_id: The user's ID

    Returns:
        A list of dicts with keys:
            - name (str): Category name
            - amount (float): Total amount spent in category
            - pct (int): Percentage of total (integer, rounded)
        Ordered by amount descending (highest first)
        Percentages are rounded and adjusted so they sum to exactly 100
        Empty list if the user has no expenses
    """
    conn = get_db()
    try:
        cursor = conn.cursor()

        # Query expenses grouped by category, ordered by amount descending
        cursor.execute(
            "SELECT category, SUM(amount) as total FROM expenses WHERE user_id = ? GROUP BY category ORDER BY total DESC",
            (user_id,)
        )
        rows = cursor.fetchall()

        # If no expenses, return empty list
        if not rows:
            return []

        # Extract categories and amounts
        categories = []
        total_amount = 0.0
        for row in rows:
            amount = row[1]
            categories.append({
                'name': row[0],
                'amount': amount
            })
            total_amount += amount

        # Calculate percentages with rounding adjustment
        breakdown = []
        rounded_percentages = []

        for category in categories:
            # Calculate raw percentage
            raw_pct = (category['amount'] / total_amount) * 100
            rounded_pct = round(raw_pct)
            rounded_percentages.append(rounded_pct)
            breakdown.append({
                'name': category['name'],
                'amount': category['amount'],
                'pct': rounded_pct
            })

        # Adjust largest category to ensure sum is exactly 100
        pct_sum = sum(rounded_percentages)
        if pct_sum != 100:
            diff = 100 - pct_sum
            # Find index of largest amount and adjust its percentage
            largest_idx = max(range(len(breakdown)), key=lambda i: breakdown[i]['amount'])
            breakdown[largest_idx]['pct'] += diff

        return breakdown
    finally:
        conn.close()
