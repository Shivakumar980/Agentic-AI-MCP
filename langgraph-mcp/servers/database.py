import os
import sqlite3
import logging
import json
from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("database_server")

# Initialize MCP
mcp = FastMCP("Database")

# Database file path
DB_FILE = "agent_database.db"

def get_db_connection():
    """Create a connection to the SQLite database."""
    # Create the database file if it doesn't exist
    conn = sqlite3.connect(DB_FILE)
    
    # Enable foreign key support
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    
    # Create default tables if they don't exist
    create_default_tables(conn)
    
    return conn

def create_default_tables(conn):
    """Create the default tables if they don't exist."""
    logger.info("Ensuring default tables exist")
    cursor = conn.cursor()
    
    # Create a simple key-value store table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS key_value_store (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create a notes table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        tags TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create a table to track created tables
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS table_registry (
        table_name TEXT PRIMARY KEY,
        schema TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()

@mcp.tool()
def create_table(table_name: str, schema: str) -> str:
    """
    Create a new table in the database with the specified schema.
    The schema should be a string describing the columns and their types.
    Example: "id INTEGER PRIMARY KEY, name TEXT, age INTEGER, email TEXT UNIQUE"
    """
    logger.info(f"Creating new table: {table_name}")
    
    # Validate table name (basic security check)
    if not table_name.isalnum() and not (table_name.startswith(tuple('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')) and all(c.isalnum() or c == '_' for c in table_name)):
        return "Invalid table name. Table names must start with a letter and contain only letters, numbers, and underscores."
    
    # Reserved table names
    reserved_tables = ['key_value_store', 'notes', 'table_registry', 'sqlite_master']
    if table_name.lower() in reserved_tables:
        return f"Cannot create table '{table_name}'. This name is reserved."
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if table already exists
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if cursor.fetchone():
            conn.close()
            return f"Table '{table_name}' already exists."
        
        # Create the table
        create_statement = f"CREATE TABLE {table_name} ({schema})"
        cursor.execute(create_statement)
        
        # Register the table
        cursor.execute(
            "INSERT INTO table_registry (table_name, schema) VALUES (?, ?)",
            (table_name, schema)
        )
        
        conn.commit()
        conn.close()
        
        result = f"Successfully created table '{table_name}'."
        logger.info(result)
        return result
    
    except Exception as e:
        error_msg = f"Error creating table: {str(e)}"
        logger.error(error_msg)
        return error_msg

@mcp.tool()
def list_tables() -> str:
    """List all tables in the database."""
    logger.info("Listing all tables")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        # Filter out system tables
        tables = [table for table in tables if not table.startswith('sqlite_')]
        
        if tables:
            result = "Available tables: " + ", ".join(tables)
        else:
            result = "No tables found in the database"
        
        logger.info(result)
        return result
    
    except Exception as e:
        error_msg = f"Error listing tables: {str(e)}"
        logger.error(error_msg)
        return error_msg

@mcp.tool()
def describe_table(table_name: str) -> str:
    """Get the schema of a specific table."""
    logger.info(f"Describing table: {table_name}")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if not cursor.fetchone():
            conn.close()
            return f"Table '{table_name}' does not exist."
        
        # Get table schema
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        conn.close()
        
        if columns:
            result = f"Schema for table '{table_name}':\n"
            result += "\n".join([f"{col[1]} ({col[2]}){' PRIMARY KEY' if col[5] else ''}" for col in columns])
            
            logger.info(f"Retrieved schema for table '{table_name}'")
            return result
        else:
            return f"No columns found for table '{table_name}'"
    
    except Exception as e:
        error_msg = f"Error describing table: {str(e)}"
        logger.error(error_msg)
        return error_msg

@mcp.tool()
def insert_record(table_name: str, fields: str, values: str) -> str:
    """
    Insert a record into a table.
    fields: Comma-separated list of column names
    values: Comma-separated list of values (surround string values with quotes)
    Example: insert_record("users", "name,age", "'John Doe',30")
    """
    logger.info(f"Inserting record into table {table_name}")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if not cursor.fetchone():
            conn.close()
            return f"Table '{table_name}' does not exist."
        
        # Insert the record
        insert_statement = f"INSERT INTO {table_name} ({fields}) VALUES ({values})"
        cursor.execute(insert_statement)
        
        # Get the rowid of the last inserted row
        last_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        result = f"Successfully inserted record into '{table_name}' with ID {last_id}."
        logger.info(result)
        return result
    
    except Exception as e:
        error_msg = f"Error inserting record: {str(e)}"
        logger.error(error_msg)
        return error_msg

@mcp.tool()
def update_record(table_name: str, set_clause: str, where_clause: str) -> str:
    """
    Update records in a table.
    set_clause: Comma-separated list of column=value assignments
    where_clause: Condition to specify which records to update
    Example: update_record("users", "age=31, status='active'", "name='John Doe'")
    """
    logger.info(f"Updating records in table {table_name}")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if not cursor.fetchone():
            conn.close()
            return f"Table '{table_name}' does not exist."
        
        # Update the records
        update_statement = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"
        cursor.execute(update_statement)
        
        # Get the number of rows affected
        rows_affected = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        result = f"Successfully updated {rows_affected} record(s) in '{table_name}'."
        logger.info(result)
        return result
    
    except Exception as e:
        error_msg = f"Error updating records: {str(e)}"
        logger.error(error_msg)
        return error_msg

@mcp.tool()
def delete_records(table_name: str, where_clause: str) -> str:
    """
    Delete records from a table.
    where_clause: Condition to specify which records to delete
    Example: delete_records("users", "status='inactive'")
    """
    logger.info(f"Deleting records from table {table_name}")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if not cursor.fetchone():
            conn.close()
            return f"Table '{table_name}' does not exist."
        
        # Delete the records
        delete_statement = f"DELETE FROM {table_name} WHERE {where_clause}"
        cursor.execute(delete_statement)
        
        # Get the number of rows affected
        rows_affected = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        result = f"Successfully deleted {rows_affected} record(s) from '{table_name}'."
        logger.info(result)
        return result
    
    except Exception as e:
        error_msg = f"Error deleting records: {str(e)}"
        logger.error(error_msg)
        return error_msg

@mcp.tool()
def query_table(table_name: str, conditions: str = "", limit: int = 10) -> str:
    """
    Query records from a table with optional conditions.
    table_name: Name of the table to query
    conditions: WHERE clause conditions (without the 'WHERE' keyword)
    limit: Maximum number of records to return
    Example: query_table("users", "age > 25", 5)
    """
    logger.info(f"Querying table {table_name}")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if not cursor.fetchone():
            conn.close()
            return f"Table '{table_name}' does not exist."
        
        # Build the query
        query = f"SELECT * FROM {table_name}"
        if conditions:
            query += f" WHERE {conditions}"
        query += f" LIMIT {limit}"
        
        # Execute the query
        cursor.execute(query)
        rows = cursor.fetchall()
        column_names = [description[0] for description in cursor.description]
        
        conn.close()
        
        if rows:
            # Format the results
            result = f"Results from '{table_name}':\n"
            
            # Header
            header = " | ".join(column_names)
            result += header + "\n"
            result += "-" * len(header) + "\n"
            
            # Rows
            for row in rows:
                formatted_row = " | ".join(str(value) for value in row)
                result += formatted_row + "\n"
            
            # Add a note if there might be more records
            if len(rows) == limit:
                result += f"\n(Showing {limit} records. There may be more.)"
            
            logger.info(f"Retrieved {len(rows)} records from '{table_name}'")
            return result
        else:
            return f"No records found in '{table_name}'" + (f" with condition: {conditions}" if conditions else "")
    
    except Exception as e:
        error_msg = f"Error querying table: {str(e)}"
        logger.error(error_msg)
        return error_msg

@mcp.tool()
def execute_safe_query(query: str) -> str:
    """
    Execute a safe SQL query (READ-ONLY for safety).
    query: The SQL query to execute
    Example: execute_safe_query("SELECT * FROM users WHERE age > 25 ORDER BY name LIMIT 10")
    """
    logger.info(f"Executing safe query: {query}")
    
    # Check if the query is trying to modify data (for safety)
    query_lower = query.lower().strip()
    dangerous_keywords = ["insert", "update", "delete", "drop", "alter", "truncate", "create", "grant"]
    
    if any(keyword in query_lower for keyword in dangerous_keywords):
        return "For security reasons, this tool only allows SELECT queries"
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(query)
        
        # Try to fetch results
        try:
            results = cursor.fetchall()
            
            if results:
                # Get column names
                column_names = [description[0] for description in cursor.description]
                
                # Format the results
                formatted_results = []
                
                # Header
                header = " | ".join(column_names)
                formatted_results.append(header)
                formatted_results.append("-" * len(header))
                
                # Rows
                for row in results:
                    formatted_row = " | ".join(str(value) for value in row)
                    formatted_results.append(formatted_row)
                
                result = "\n".join(formatted_results)
                if len(result) > 1500:  # Truncate if too long
                    result = result[:1500] + "...\n(Results truncated)"
            else:
                result = "Query executed successfully, but returned no results"
        except sqlite3.Error:
            # No results to fetch
            result = "Query executed successfully"
        
        conn.close()
        
        logger.info(f"Query executed successfully")
        return result
    
    except Exception as e:
        error_msg = f"Error executing query: {str(e)}"
        logger.error(error_msg)
        return error_msg

@mcp.tool()
def delete_table(table_name: str) -> str:
    """Delete a table from the database."""
    logger.info(f"Deleting table: {table_name}")
    
    # Protect default tables
    protected_tables = ['key_value_store', 'notes', 'table_registry', 'sqlite_master']
    if table_name.lower() in protected_tables:
        return f"Cannot delete table '{table_name}'. This is a system table."
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if not cursor.fetchone():
            conn.close()
            return f"Table '{table_name}' does not exist."
        
        # Delete the table
        cursor.execute(f"DROP TABLE {table_name}")
        
        # Remove from registry
        cursor.execute("DELETE FROM table_registry WHERE table_name = ?", (table_name,))
        
        conn.commit()
        conn.close()
        
        result = f"Successfully deleted table '{table_name}'."
        logger.info(result)
        return result
    
    except Exception as e:
        error_msg = f"Error deleting table: {str(e)}"
        logger.error(error_msg)
        return error_msg

@mcp.tool()
def store_value(key: str, value: str) -> str:
    """Store a value with the given key in the database."""
    logger.info(f"Storing value for key: {key}")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if key already exists
        cursor.execute("SELECT key FROM key_value_store WHERE key = ?", (key,))
        if cursor.fetchone():
            # Update existing record
            cursor.execute(
                "UPDATE key_value_store SET value = ?, updated_at = CURRENT_TIMESTAMP WHERE key = ?",
                (value, key)
            )
            result = f"Updated value for key '{key}'"
        else:
            # Insert new record
            cursor.execute(
                "INSERT INTO key_value_store (key, value) VALUES (?, ?)",
                (key, value)
            )
            result = f"Stored new value for key '{key}'"
        
        conn.commit()
        conn.close()
        logger.info(result)
        return result
    
    except Exception as e:
        error_msg = f"Error storing value: {str(e)}"
        logger.error(error_msg)
        return error_msg

@mcp.tool()
def get_value(key: str) -> str:
    """Retrieve a value for the given key from the database."""
    logger.info(f"Retrieving value for key: {key}")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT value FROM key_value_store WHERE key = ?", (key,))
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            logger.info(f"Found value for key '{key}': {result['value']}")
            return result["value"]
        else:
            logger.info(f"No value found for key '{key}'")
            return f"No value found for key '{key}'"
    
    except Exception as e:
        error_msg = f"Error retrieving value: {str(e)}"
        logger.error(error_msg)
        return error_msg

@mcp.tool()
def list_keys() -> str:
    """List all available keys in the database."""
    logger.info("Listing all keys")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT key FROM key_value_store ORDER BY key")
        keys = [row["key"] for row in cursor.fetchall()]
        
        conn.close()
        
        if keys:
            result = "Available keys: " + ", ".join(keys)
        else:
            result = "No keys found in the database"
        
        logger.info(result)
        return result
    
    except Exception as e:
        error_msg = f"Error listing keys: {str(e)}"
        logger.error(error_msg)
        return error_msg

@mcp.tool()
def add_note(title: str, content: str, tags: str = "") -> str:
    """Add a new note to the database."""
    logger.info(f"Adding new note: {title}")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO notes (title, content, tags) VALUES (?, ?, ?)",
            (title, content, tags)
        )
        
        note_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        result = f"Added note with ID {note_id}"
        logger.info(result)
        return result
    
    except Exception as e:
        error_msg = f"Error adding note: {str(e)}"
        logger.error(error_msg)
        return error_msg

@mcp.tool()
def get_note(note_id: int) -> str:
    """Retrieve a note by its ID."""
    logger.info(f"Retrieving note with ID: {note_id}")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
        note = cursor.fetchone()
        
        conn.close()
        
        if note:
            result = f"Title: {note['title']}\nContent: {note['content']}"
            if note['tags']:
                result += f"\nTags: {note['tags']}"
            logger.info(f"Found note with ID {note_id}")
            return result
        else:
            logger.info(f"No note found with ID {note_id}")
            return f"No note found with ID {note_id}"
    
    except Exception as e:
        error_msg = f"Error retrieving note: {str(e)}"
        logger.error(error_msg)
        return error_msg

@mcp.tool()
def search_notes(query: str) -> str:
    """Search for notes by title, content, or tags."""
    logger.info(f"Searching notes for: {query}")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Search in title, content, and tags
        cursor.execute(
            "SELECT id, title FROM notes WHERE title LIKE ? OR content LIKE ? OR tags LIKE ?",
            (f"%{query}%", f"%{query}%", f"%{query}%")
        )
        
        results = cursor.fetchall()
        conn.close()
        
        if results:
            result_list = [f"ID: {row['id']} - Title: {row['title']}" for row in results]
            result = "Found notes:\n" + "\n".join(result_list)
            logger.info(f"Found {len(results)} notes matching '{query}'")
            return result
        else:
            logger.info(f"No notes found matching '{query}'")
            return f"No notes found matching '{query}'"
    
    except Exception as e:
        error_msg = f"Error searching notes: {str(e)}"
        logger.error(error_msg)
        return error_msg

if __name__ == "__main__":
    logger.info("Starting database server with STDIO transport")
    # Ensure the database connection works
    conn = get_db_connection()
    conn.close()
    # Run the MCP server with STDIO transport
    mcp.run(transport="stdio")