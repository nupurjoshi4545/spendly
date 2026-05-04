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


def get_recent_transactions(user_id, limit=10, date_from=None, date_to=None):
    conn = get_db()
    try:
        cursor = conn.cursor()
        filtering = date_from is not None or date_to is not None

        sql = "SELECT id, date, description, category, amount FROM expenses WHERE user_id = ?"
        params = [user_id]
        if date_from:
            sql += " AND date >= ?"
            params.append(date_from)
        if date_to:
            sql += " AND date <= ?"
            params.append(date_to)
        sql += " ORDER BY date DESC"
        if not filtering:
            sql += " LIMIT ?"
            params.append(limit)

        cursor.execute(sql, params)
        rows = cursor.fetchall()

        transactions = []
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


def get_summary_stats(user_id, date_from=None, date_to=None):
    conn = get_db()
    try:
        cursor = conn.cursor()

        date_clause = ""
        date_params = []
        if date_from:
            date_clause += " AND date >= ?"
            date_params.append(date_from)
        if date_to:
            date_clause += " AND date <= ?"
            date_params.append(date_to)

        cursor.execute(
            f"SELECT SUM(amount) FROM expenses WHERE user_id = ?{date_clause}",
            [user_id] + date_params
        )
        total_spent = cursor.fetchone()[0] or 0.0

        cursor.execute(
            f"SELECT COUNT(*) FROM expenses WHERE user_id = ?{date_clause}",
            [user_id] + date_params
        )
        transaction_count = cursor.fetchone()[0] or 0

        cursor.execute(
            f"SELECT category FROM expenses WHERE user_id = ?{date_clause} GROUP BY category ORDER BY SUM(amount) DESC LIMIT 1",
            [user_id] + date_params
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


def get_category_breakdown(user_id, date_from=None, date_to=None):
    conn = get_db()
    try:
        cursor = conn.cursor()

        date_clause = ""
        date_params = []
        if date_from:
            date_clause += " AND date >= ?"
            date_params.append(date_from)
        if date_to:
            date_clause += " AND date <= ?"
            date_params.append(date_to)

        cursor.execute(
            f"SELECT category, SUM(amount) as total FROM expenses WHERE user_id = ?{date_clause} GROUP BY category ORDER BY total DESC",
            [user_id] + date_params
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
