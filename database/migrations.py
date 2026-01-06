def migrations_sql():
    return [
        """
        CREATE TABLE IF NOT EXISTS executed_commands (
            id INTEGER PRIMARY KEY,
            order_id INTEGER UNIQUE,
            symbol TEXT,
            side TEXT,
            order_type TEXT,
            master_qty REAL,
            terminal_qty REAL,
            terminal_price REAL,
            status TEXT,
            exchange_order_id TEXT,
            executed_at TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY,
            master_trade_id INTEGER,
            server_trade_id INTEGER,
            symbol TEXT,
            side TEXT,
            entry_qty REAL,
            entry_price REAL,
            exit_qty REAL,
            exit_price REAL,
            pnl REAL,
            status TEXT,
            opened_at TIMESTAMP,
            closed_at TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY,
            level TEXT,
            message TEXT,
            data TEXT,
            created_at TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS symbols (
            symbol TEXT PRIMARY KEY,
            min_order_qty REAL,
            min_price REAL,
            tick_size REAL,
            step_size REAL,
            status INTEGER DEFAULT 1,
            updated_at TIMESTAMP
        );
        """
    ]


def run_migrations(db):
    for sql in migrations_sql():
        db.execute(sql)