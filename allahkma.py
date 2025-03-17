import sqlite3
import os
from datetime import datetime, timedelta
import streamlit as st

class LibraryDatabase:
    def __init__(self, db_name="library.db"):
        """Initialize the database connection and create tables if they don't exist."""
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()
    
    def create_tables(self):
        """Create necessary tables for the library management system."""
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            isbn TEXT UNIQUE,
            publication_year INTEGER,
            genre TEXT,
            added_date TEXT,
            status TEXT DEFAULT 'available'
        )
        ''')
        
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS borrowers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE,
            phone TEXT,
            registration_date TEXT
        )
        ''')
        
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS loans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER,
            borrower_id INTEGER,
            loan_date TEXT,
            due_date TEXT,
            return_date TEXT,
            FOREIGN KEY (book_id) REFERENCES books (id),
            FOREIGN KEY (borrower_id) REFERENCES borrowers (id)
        )
        ''')
        
        self.conn.commit()
    
    def add_book(self, title, author, isbn=None, publication_year=None, genre=None):
        """Add a new book to the database."""
        try:
            added_date = datetime.now().strftime("%Y-%m-%d")
            self.cursor.execute('''
            INSERT INTO books (title, author, isbn, publication_year, genre, added_date, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (title, author, isbn, publication_year, genre, added_date, 'available'))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            print(f"Error: Book with ISBN {isbn} already exists.")
            return False
    
    def search_books(self, query, search_by="title"):
        """Search for books by title, author, or ISBN."""
        search_query = f"%{query}%"
        if search_by == "title":
            self.cursor.execute("SELECT * FROM books WHERE title LIKE ?", (search_query,))
        elif search_by == "author":
            self.cursor.execute("SELECT * FROM books WHERE author LIKE ?", (search_query,))
        elif search_by == "isbn":
            self.cursor.execute("SELECT * FROM books WHERE isbn LIKE ?", (search_query,))
        elif search_by == "genre":
            self.cursor.execute("SELECT * FROM books WHERE genre LIKE ?", (search_query,))
        else:
            return []
        
        return self.cursor.fetchall()
    
    def register_borrower(self, name, email, phone=None):
        """Register a new borrower."""
        try:
            registration_date = datetime.now().strftime("%Y-%m-%d")
            self.cursor.execute('''
            INSERT INTO borrowers (name, email, phone, registration_date)
            VALUES (?, ?, ?, ?)
            ''', (name, email, phone, registration_date))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            print(f"Error: Borrower with email {email} already exists.")
            return False
    
    def loan_book(self, book_id, borrower_id, loan_period_days=14):
        """Loan a book to a borrower."""
        # Check if book is available
        self.cursor.execute("SELECT status FROM books WHERE id = ?", (book_id,))
        result = self.cursor.fetchone()
        if not result or result[0] != 'available':
            print("Error: Book is not available for loan.")
            return False
        
        loan_date = datetime.now()
        due_date = loan_date + timedelta(days=loan_period_days)
        
        # Update book status
        self.cursor.execute("UPDATE books SET status = 'loaned' WHERE id = ?", (book_id,))
        
        # Record the loan
        self.cursor.execute('''
        INSERT INTO loans (book_id, borrower_id, loan_date, due_date)
        VALUES (?, ?, ?, ?)
        ''', (book_id, borrower_id, loan_date.strftime("%Y-%m-%d"), due_date.strftime("%Y-%m-%d")))
        
        self.conn.commit()
        return True
    
    def return_book(self, loan_id):
        """Process a book return."""
        self.cursor.execute("SELECT book_id FROM loans WHERE id = ?", (loan_id,))
        result = self.cursor.fetchone()
        if not result:
            print("Error: Loan record not found.")
            return False
        
        book_id = result[0]
        return_date = datetime.now().strftime("%Y-%m-%d")
        
        # Update loan record
        self.cursor.execute("UPDATE loans SET return_date = ? WHERE id = ?", (return_date, loan_id))
        
        # Update book status
        self.cursor.execute("UPDATE books SET status = 'available' WHERE id = ?", (book_id,))
        
        self.conn.commit()
        return True
    
    def get_overdue_loans(self):
        """Get a list of all overdue loans."""
        today = datetime.now().strftime("%Y-%m-%d")
        self.cursor.execute('''
        SELECT loans.id, books.title, borrowers.name, loans.due_date
        FROM loans
        JOIN books ON loans.book_id = books.id
        JOIN borrowers ON loans.borrower_id = borrowers.id
        WHERE loans.due_date < ? AND loans.return_date IS NULL
        ''', (today,))
        
        return self.cursor.fetchall()
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()

# Streamlit app
def main():
    # Set page configuration
    st.set_page_config(
        page_title="Library Management System",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for styling
    st.markdown("""
    <style>
    .main-header {
        font-size: 3.5rem !important;
        color: #1E88E5 !important;
        text-align: center;
        margin-bottom: 2.5rem;
        text-shadow: 3px 3px 5px rgba(0,0,0,0.15);
        font-weight: bold;
    }
    .sub-header {
        font-size: 2.2rem !important;
        color: #0D47A1 !important;
        border-bottom: 3px solid #1E88E5;
        padding-bottom: 0.7rem;
        margin-bottom: 2rem;
        font-weight: 600;
    }
    .success-msg {
        background-color: #E8F5E9;
        padding: 1.2rem;
        border-radius: 8px;
        border-left: 6px solid #4CAF50;
        margin: 1rem 0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .error-msg {
        background-color: #FFEBEE;
        padding: 1.2rem;
        border-radius: 8px;
        border-left: 6px solid #F44336;
        margin: 1rem 0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .warning-msg {
        background-color: #FFF8E1;
        padding: 1.2rem;
        border-radius: 8px;
        border-left: 6px solid #FFC107;
        margin: 1rem 0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .info-msg {
        background-color: #E3F2FD;
        padding: 1.2rem;
        border-radius: 8px;
        border-left: 6px solid #2196F3;
        margin: 1rem 0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .book-card {
        background-color: #F8F9FA;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        transition: transform 0.3s ease;
    }
    .book-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    .sidebar .css-1d391kg {
        background-color: #E3F2FD;
        border-radius: 10px;
    }
    button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1) !important;
        transition: all 0.3s ease !important;
    }
    button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.15) !important;
    }
    .stTextInput, .stNumberInput, .stSelectbox {
        margin-bottom: 1rem;
    }
    .stTextInput > div, .stNumberInput > div, .stSelectbox > div {
        border-radius: 8px !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Title with custom styling
    st.markdown("<h1 class='main-header'>📚 Library Management System</h1>", unsafe_allow_html=True)
    
    db = LibraryDatabase()
    
    # Sidebar with improved styling
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/library-building.png", width=120)
        st.markdown("### 📋 Navigation Menu")
        menu = ["Home", "Add Book", "Search Books", "Register Borrower", "Loan Book", "Return Book", "Overdue Loans"]
        choice = st.selectbox("", menu)
    
    if choice == "Home":
        st.markdown("<h2 class='sub-header'>Welcome to the Library Management System</h2>", unsafe_allow_html=True)
        
        # Dashboard layout with columns
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📖 Quick Access")
            st.markdown("""
            * **Add new books** to the library collection
            * **Search books** by title, author, ISBN, or genre
            * **Register new borrowers** to the system
            """)
            
        with col2:
            st.markdown("### 🔍 System Features")
            st.markdown("""
            * **Loan books** to registered borrowers
            * **Return books** and update availability
            * **Track overdue loans** for better management
            """)
        
        # System statistics
        st.markdown("<h3 style='margin-top: 2.5rem; color: #0D47A1; border-bottom: 2px solid #1E88E5; padding-bottom: 0.5rem;'>System Statistics</h3>", unsafe_allow_html=True)
        
        # Create a row of metrics
        col1, col2, col3 = st.columns(3)
        
        # Get counts from database
        db.cursor.execute("SELECT COUNT(*) FROM books")
        book_count = db.cursor.fetchone()[0]
        
        db.cursor.execute("SELECT COUNT(*) FROM borrowers")
        borrower_count = db.cursor.fetchone()[0]
        
        db.cursor.execute("SELECT COUNT(*) FROM loans WHERE return_date IS NULL")
        active_loans = db.cursor.fetchone()[0]
        
        col1.metric("Total Books", book_count)
        col2.metric("Registered Borrowers", borrower_count)
        col3.metric("Active Loans", active_loans)
        
    elif choice == "Add Book":
        st.markdown("<h2 class='sub-header'>Add New Book</h2>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input("Title")
            author = st.text_input("Author")
            isbn = st.text_input("ISBN")
        
        with col2:
            year = st.number_input("Publication Year", min_value=1000, max_value=datetime.now().year, step=1)
            genre = st.text_input("Genre")
        
        if st.button("Add Book", key="add_book_btn"):
            if title and author:
                if db.add_book(title, author, isbn, year, genre):
                    st.markdown(f"<div class='success-msg'>Book '{title}' added successfully!</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='error-msg'>Failed to add book. ISBN might already exist.</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='warning-msg'>Title and Author are required fields.</div>", unsafe_allow_html=True)
    
    elif choice == "Search Books":
        st.markdown("<h2 class='sub-header'>Search Books</h2>", unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            search_by = st.selectbox("Search By", ["title", "author", "isbn", "genre"])
            query = st.text_input("Enter search term")
        
        with col2:
            if query:
                results = db.search_books(query, search_by)
                if results:
                    for book in results:
                        st.markdown(f"""
                        <div class='book-card'>
                            <h3>{book[1]}</h3>
                            <p><strong>Author:</strong> {book[2]}</p>
                            <p><strong>ISBN:</strong> {book[3] or 'N/A'} | <strong>Year:</strong> {book[4] or 'N/A'} | <strong>Genre:</strong> {book[5] or 'N/A'}</p>
                            <p><strong>Status:</strong> <span style="color: {'green' if book[7] == 'available' else 'red'};">{book[7]}</span></p>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown("<div class='info-msg'>No books found matching your search criteria.</div>", unsafe_allow_html=True)
    
    elif choice == "Register Borrower":
        st.markdown("<h2 class='sub-header'>Register New Borrower</h2>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Name")
        
        with col2:
            email = st.text_input("Email")
            
        phone = st.text_input("Phone")
        
        if st.button("Register", key="register_btn"):
            if name and email:
                if db.register_borrower(name, email, phone):
                    st.markdown(f"<div class='success-msg'>Borrower '{name}' registered successfully!</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='error-msg'>Failed to register borrower. Email might already exist.</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='warning-msg'>Name and Email are required fields.</div>", unsafe_allow_html=True)
    
    elif choice == "Loan Book":
        st.markdown("<h2 class='sub-header'>Loan a Book</h2>", unsafe_allow_html=True)
        
        # Get available books
        db.cursor.execute("SELECT id, title FROM books WHERE status = 'available'")
        available_books = db.cursor.fetchall()
        book_options = {book[1]: book[0] for book in available_books}
        
        # Get registered borrowers
        db.cursor.execute("SELECT id, name FROM borrowers")
        borrowers = db.cursor.fetchall()
        borrower_options = {borrower[1]: borrower[0] for borrower in borrowers}
        
        col1, col2 = st.columns(2)
        
        with col1:
            selected_book = st.selectbox("Select Book", list(book_options.keys()) if book_options else ["No books available"])
        
        with col2:
            selected_borrower = st.selectbox("Select Borrower", list(borrower_options.keys()) if borrower_options else ["No borrowers registered"])
        
        loan_days = st.slider("Loan Period (Days)", 7, 30, 14)
        
        if st.button("Loan Book", key="loan_book_btn"):
            if book_options and borrower_options:  # Check if we have books and borrowers
                if selected_book in book_options and selected_borrower in borrower_options:
                    book_id = book_options[selected_book]
                    borrower_id = borrower_options[selected_borrower]
                    if db.loan_book(book_id, borrower_id, loan_days):
                        st.markdown(f"<div class='success-msg'>Book '{selected_book}' loaned to {selected_borrower} successfully!</div>", unsafe_allow_html=True)
                    else:
                        st.markdown("<div class='error-msg'>Failed to loan book.</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='warning-msg'>Please select both a book and a borrower.</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='warning-msg'>No books available or no borrowers registered.</div>", unsafe_allow_html=True)
    
    elif choice == "Return Book":
        st.markdown("<h2 class='sub-header'>Return a Book</h2>", unsafe_allow_html=True)
        
        # Get active loans
        db.cursor.execute("""
        SELECT loans.id, books.title, borrowers.name, loans.due_date
        FROM loans
        JOIN books ON loans.book_id = books.id
        JOIN borrowers ON loans.borrower_id = borrowers.id
        WHERE loans.return_date IS NULL
        """)
        active_loans = db.cursor.fetchall()
        
        if active_loans:
            loan_options = {f"{loan[1]} (borrowed by {loan[2]}, due {loan[3]})": loan[0] for loan in active_loans}
            selected_loan = st.selectbox("Select Loan to Return", list(loan_options.keys()))
            
            if st.button("Return Book", key="return_book_btn"):
                loan_id = loan_options[selected_loan]
                if db.return_book(loan_id):
                    st.markdown("<div class='success-msg'>Book returned successfully!</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='error-msg'>Failed to process return.</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='info-msg'>No active loans found.</div>", unsafe_allow_html=True)
    
    elif choice == "Overdue Loans":
        st.markdown("<h2 class='sub-header'>Overdue Loans</h2>", unsafe_allow_html=True)
        
        overdue_loans = db.get_overdue_loans()
        
        if overdue_loans:
            for loan in overdue_loans:
                days_overdue = (datetime.now() - datetime.strptime(loan[3], "%Y-%m-%d")).days
                st.markdown(f"""
                <div class='book-card' style='border-left: 5px solid #F44336;'>
                    <h3>{loan[1]}</h3>
                    <p><strong>Borrowed by:</strong> {loan[2]}</p>
                    <p><strong>Due date:</strong> {loan[3]} <span style='color: red;'>({days_overdue} days overdue)</span></p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("<div class='info-msg'>No overdue loans found.</div>", unsafe_allow_html=True)
    
    # Footer
    st.markdown("""
    <div style='text-align: center; margin-top: 4rem; padding: 1.5rem; background-color: #F8F9FA; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);'>
        <p style='font-size: 1.1rem;'>© 2023 Library Management System | Developed with ❤️ using Streamlit | Created by Dilsher Khaskhelii</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Close the database connection when the app is done
    db.close()

if __name__ == "__main__":
    main()
