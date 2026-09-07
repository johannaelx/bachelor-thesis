from backend.app.database import SessionLocal
from backend.app.models.deck import Deck
from backend.app.models.item import Item

def seed():
    db = SessionLocal()
    try:
        deck = Deck(name="Grundvokabular")
        db.add(deck)
        db.flush()

        items = [
            Item(german="Haus",   english="house",  deck_id=deck.id),
            Item(german="Auto",   english="car",    deck_id=deck.id),
            Item(german="Hund",   english="dog",    deck_id=deck.id),
        ]
        db.add_all(items)
        db.commit()
        print(f"Seeded {len(items)} items into deck '{deck.name}'")
    finally:
        db.close()

if __name__ == "__main__":
    seed()