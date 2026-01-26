"""
Transaction Tracker
Tracks items dispensed in current transaction and calculates totals
"""

from typing import List, Dict
from datetime import datetime


class TransactionTracker:
    """
    Tracks items dispensed in a single transaction
    
    Maintains list of items dispensed, calculates running total,
    and generates transaction summaries.
    """
    
    def __init__(self):
        """Initialize empty transaction"""
        self.items: List[Dict] = []
        self.total: float = 0.0
        self.start_time = datetime.now()
    
    def add_item(self, product_id: str, product_name: str, 
                 quantity: float, unit: str, price: float) -> None:
        """
        Add dispensed item to transaction
        
        Args:
            product_id: Product identifier
            product_name: Product display name
            quantity: Amount dispensed
            unit: Unit type (oz, ml, etc.)
            price: Price for this item in dollars
        """
        item = {
            "product_id": product_id,
            "product_name": product_name,
            "quantity": round(quantity, 2),
            "unit": unit,
            "price": round(price, 2)
        }
        
        self.items.append(item)
        self.total = round(self.total + price, 2)
    
    def get_total(self) -> float:
        """
        Get total transaction price in dollars
        
        Returns:
            Total price (rounded to 2 decimal places)
        """
        return round(self.total, 2)
    
    def get_total_cents(self) -> int:
        """
        Get total transaction price in cents
        
        Returns:
            Total price in cents (for ePort protocol)
        """
        return int(round(self.total * 100))
    
    def get_items(self) -> List[Dict]:
        """
        Get list of items in transaction
        
        Returns:
            List of item dictionaries
        """
        return self.items.copy()
    
    def get_item_count(self) -> int:
        """Get number of items in transaction"""
        return len(self.items)
    
    def is_empty(self) -> bool:
        """Check if transaction has no items"""
        return len(self.items) == 0
    
    def get_summary(self) -> str:
        """
        Generate human-readable transaction summary
        
        Returns:
            Multi-line string with itemized list and total
        """
        if self.is_empty():
            return "No items dispensed"
        
        lines = []
        lines.append("TRANSACTION SUMMARY")
        lines.append("-" * 40)
        
        for item in self.items:
            # Format: "Hand Soap: 2.50 oz - $0.38"
            lines.append(
                f"{item['product_name']}: "
                f"{item['quantity']:.2f} {item['unit']} - "
                f"${item['price']:.2f}"
            )
        
        lines.append("-" * 40)
        lines.append(f"TOTAL: ${self.total:.2f}")
        
        return "\n".join(lines)
    
    def get_compact_summary(self) -> str:
        """
        Generate compact summary for display
        
        Returns:
            Single-line summary (e.g., "3 items, $0.76")
        """
        if self.is_empty():
            return "Empty transaction"
        
        item_count = len(self.items)
        item_word = "item" if item_count == 1 else "items"
        return f"{item_count} {item_word}, ${self.total:.2f}"
    
    def get_eport_description(self) -> str:
        """
        Generate description for ePort transaction result (max 30 bytes)
        
        Returns:
            Truncated description for ePort protocol
        """
        if self.is_empty():
            return "No items"
        
        if len(self.items) == 1:
            # Single item: "2.50 oz hand soap"
            item = self.items[0]
            desc = f"{item['quantity']:.2f} {item['unit']} {item['product_name'].lower()}"
        else:
            # Multiple items: "3 items: soap, detergent"
            product_names = [item['product_name'].split()[0] for item in self.items]
            products_str = ", ".join(product_names[:2])  # First 2 products
            if len(self.items) > 2:
                products_str += "..."
            desc = f"{len(self.items)} items: {products_str}"
        
        # Truncate to 30 bytes (ePort limit)
        return desc[:30]
    
    def reset(self) -> None:
        """Reset transaction for next customer"""
        self.items.clear()
        self.total = 0.0
        self.start_time = datetime.now()
    
    def __repr__(self) -> str:
        """String representation for debugging"""
        return f"TransactionTracker({len(self.items)} items, ${self.total:.2f})"
    
    def __str__(self) -> str:
        """Human-readable string"""
        return self.get_compact_summary()
