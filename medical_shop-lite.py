"""
=====================================================
JoyBoy MEDICARE - Medical Shop Management System
=====================================================

This is a console-based medical shop system built using:
- Python
- SQLite Database
- OOP (Object Oriented Programming)

Main Features:
1. Inventory Management
2. Order Management
3. Receipt Generation
4. Sales Summary
5. Inventory Logs

Database file (medical_shop.db) will be created automatically.

Author: Your Name
=====================================================
"""

# Import required libraries
import sqlite3              # For database
from datetime import datetime   # For date and time
import os                   # To clear screen


# --------------------------------------------------
# DATABASE CLASS
# --------------------------------------------------

class MedicalShopDB:
    """
    This class handles:
    - Database connection
    - Table creation
    - Initial default medicines
    """

    def __init__(self, db_name="medical_shop.db"):
        self.db_name = db_name
        self.conn = None
        self.cursor = None
        self.connect()          # Connect to database
        self.create_tables()    # Create required tables
        self.initialize_inventory()  # Add default medicines

    def connect(self):
        """Connect to SQLite database"""
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()

    def create_tables(self):
        """
        Create required tables if they do not exist.
        """

        # Table 1: Medicines
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS medicines (
            medicine_id INTEGER PRIMARY KEY AUTOINCREMENT,
            medicine_name TEXT NOT NULL,
            medicine_type TEXT NOT NULL,
            price REAL NOT NULL,
            stock_quantity INTEGER NOT NULL,
            reorder_level INTEGER DEFAULT 10,
            expiry_date TEXT,
            manufacturer TEXT,
            last_updated TEXT
        )
        """)

        # Table 2: Orders
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            receipt_number INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            order_date TEXT NOT NULL,
            total_amount REAL NOT NULL,
            payment_status TEXT DEFAULT 'Pending'
        )
        """)

        # Table 3: Order Items
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            receipt_number INTEGER,
            medicine_id INTEGER,
            quantity INTEGER,
            price_per_unit REAL,
            total_price REAL
        )
        """)

        self.conn.commit()

    def initialize_inventory(self):
        """
        Add some default medicines only if table is empty.
        """

        self.cursor.execute("SELECT COUNT(*) FROM medicines")
        count = self.cursor.fetchone()[0]

        if count == 0:
            medicines = [
                ("Paracetamol", "Tablet", 10.0, 100, 10, "2026-12-31", "ABC Pharma"),
                ("Amoxicillin", "Capsule", 20.0, 80, 10, "2026-11-30", "XYZ Pharma"),
                ("Cough Syrup", "Syrup", 50.0, 60, 10, "2026-10-30", "HealthCare Ltd")
            ]

            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            for med in medicines:
                self.cursor.execute("""
                INSERT INTO medicines 
                (medicine_name, medicine_type, price, stock_quantity, 
                reorder_level, expiry_date, manufacturer, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (*med, current_time))

            self.conn.commit()

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


# --------------------------------------------------
# INVENTORY MANAGEMENT CLASS
# --------------------------------------------------

class InventoryManager:
    """
    This class manages:
    - View inventory
    - Add medicine
    - Update stock
    """

    def __init__(self, db):
        self.db = db

    def view_inventory(self):
        """Display all medicines available in stock"""

        clear_screen()
        print("\n----- CURRENT INVENTORY -----\n")

        self.db.cursor.execute("SELECT * FROM medicines")
        medicines = self.db.cursor.fetchall()

        for med in medicines:
            print(f"ID: {med[0]} | Name: {med[1]} | Price: ₹{med[3]} | Stock: {med[4]}")

    def add_medicine(self):
        """Add new medicine to inventory"""

        name = input("Enter Medicine Name: ")
        med_type = input("Enter Type: ")
        price = float(input("Enter Price: "))
        stock = int(input("Enter Stock Quantity: "))

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.db.cursor.execute("""
        INSERT INTO medicines
        (medicine_name, medicine_type, price, stock_quantity, last_updated)
        VALUES (?, ?, ?, ?, ?)
        """, (name, med_type, price, stock, current_time))

        self.db.conn.commit()
        print("Medicine added successfully!")

    def update_stock(self):
        """Update stock quantity of existing medicine"""

        med_id = int(input("Enter Medicine ID: "))
        new_stock = int(input("Enter New Stock Quantity: "))

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.db.cursor.execute("""
        UPDATE medicines
        SET stock_quantity = ?, last_updated = ?
        WHERE medicine_id = ?
        """, (new_stock, current_time, med_id))

        self.db.conn.commit()
        print("Stock updated successfully!")


# --------------------------------------------------
# ORDER MANAGEMENT CLASS
# --------------------------------------------------

class OrderManager:
    """
    This class handles:
    - Taking orders
    - Generating receipts
    - Updating stock after sale
    """

    def __init__(self, db):
        self.db = db

    def take_order(self):
        """Create a new customer order"""

        customer = input("Enter Customer Name: ")
        order_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Create new order
        self.db.cursor.execute("""
        INSERT INTO orders (customer_name, order_date, total_amount)
        VALUES (?, ?, 0)
        """, (customer, order_date))

        receipt_no = self.db.cursor.lastrowid
        total_amount = 0

        while True:
            med_id = input("Enter Medicine ID (0 to finish): ")

            if med_id == "0":
                break

            med_id = int(med_id)
            quantity = int(input("Enter Quantity: "))

            # Get medicine price and stock
            self.db.cursor.execute("""
            SELECT price, stock_quantity FROM medicines
            WHERE medicine_id = ?
            """, (med_id,))

            result = self.db.cursor.fetchone()

            if result:
                price, stock = result

                if quantity <= stock:
                    item_total = price * quantity
                    total_amount += item_total

                    # Insert into order_items
                    self.db.cursor.execute("""
                    INSERT INTO order_items
                    (receipt_number, medicine_id, quantity, price_per_unit, total_price)
                    VALUES (?, ?, ?, ?, ?)
                    """, (receipt_no, med_id, quantity, price, item_total))

                    # Reduce stock
                    self.db.cursor.execute("""
                    UPDATE medicines
                    SET stock_quantity = stock_quantity - ?
                    WHERE medicine_id = ?
                    """, (quantity, med_id))

                else:
                    print("Not enough stock available!")

        # Update total amount
        self.db.cursor.execute("""
        UPDATE orders
        SET total_amount = ?
        WHERE receipt_number = ?
        """, (total_amount, receipt_no))

        self.db.conn.commit()

        print(f"\nOrder created successfully! Receipt No: {receipt_no}")
        print(f"Total Amount: ₹{total_amount}")


# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------

def clear_screen():
    """Clear terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')


def main_menu():
    """Display main menu options"""

    print("\n===== JOYBOY MEDICARE =====")
    print("1. Take Order")
    print("2. View Inventory")
    print("3. Add Medicine")
    print("4. Update Stock")
    print("5. Exit")


# --------------------------------------------------
# MAIN FUNCTION
# --------------------------------------------------

def main():
    """Main program loop"""

    db = MedicalShopDB()
    order_manager = OrderManager(db)
    inventory_manager = InventoryManager(db)

    while True:
        main_menu()
        choice = input("Enter choice: ")

        if choice == "1":
            order_manager.take_order()
        elif choice == "2":
            inventory_manager.view_inventory()
        elif choice == "3":
            inventory_manager.add_medicine()
        elif choice == "4":
            inventory_manager.update_stock()
        elif choice == "5":
            print("Exiting application...")
            break
        else:
            print("Invalid choice!")

    db.close()


# Run program
if __name__ == "__main__":
    main()
