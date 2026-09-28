from backend.app.database import SessionLocal
from backend.app.models.user import User
from backend.app.models.deck import Deck
from backend.app.models.item import Item


def get_or_create_user(db, name: str) -> User:
    """Returns the existing user with this name or creates a new one."""
    user = db.query(User).filter_by(name=name).first()
    if user:
        return user
    user = User(name=name)
    db.add(user)
    db.flush()
    return user


def get_or_create_deck(db, name: str) -> Deck:
    """Returns the existing deck with this name or creates a new one."""
    deck = db.query(Deck).filter_by(name=name).first()
    if deck:
        return deck
    deck = Deck(name=name)
    db.add(deck)
    db.flush()
    return deck


def get_or_create_item(db, german: str, english: str, deck_id: int) -> tuple[Item, bool]:
    """
    Returns the existing item (matched by german word + deck) or creates a new one.
    """
    item = db.query(Item).filter_by(german=german, deck_id=deck_id).first()
    if item:
        return item, False
    item = Item(german=german, english=english, deck_id=deck_id)
    db.add(item)
    return item, True


def seed_deck(db, deck_name: str, words: list[tuple[str, str]]) -> tuple[Deck, int]:
    """Creates or reuses a deck and seeds it with the given (german, english) word pairs."""
    deck = get_or_create_deck(db, deck_name)
    created = 0
    for german, english in words:
        _, was_created = get_or_create_item(db, german, english, deck.id)
        if was_created:
            created += 1
    return deck, created


def seed():
    db = SessionLocal()
    try:
        user = get_or_create_user(db, "Testnutzer")

        deck, created = seed_deck(db, "Grundvokabular", [
            ("Haus", "house"),
            ("Auto", "car"),
            ("Hund", "dog"),
        ])
        db.commit()
        print(f"Seeded user '{user.name}' (id={user.id})")
        print(f"Deck '{deck.name}': {created} new item(s) added")

        deck_environment, created_environment = seed_deck(db, "Umweltschutz & Nachhaltigkeit", [
            ("Nachhaltigkeit", "sustainability"),
            ("vermeiden", "to avoid"),
            ("verringern", "to reduce"),
            ("erneuerbar", "renewable"),
            ("Klimawandel", "climate change"),
            ("sparen", "to save / conserve"),
            ("verbrauchen", "to consume / use up"),
            ("umweltfreundlich", "environmentally friendly"),
            ("schützen", "to protect"),
            ("Einfluss", "influence / impact"),
        ])
        db.commit()
        print(f"Deck '{deck_environment.name}': {created_environment} new item(s) added")

        deck_mix, created_mix = seed_deck(db, "Mix", [
            ("Voraussetzung", "requirement / prerequisite"),
            ("überzeugen", "to convince"),
            ("spontan", "spontaneous"),
            ("Herausforderung", "challenge"),
            ("enttäuscht", "disappointed"),
            ("beschweren", "to complain"),
            ("Gelegenheit", "opportunity / occasion"),
            ("vergleichen", "to compare"),
            ("pünktlich", "punctual / on time"),
            ("Vereinbarung", "agreement"),
        ])
        db.commit()
        print(f"Deck '{deck_mix.name}': {created_mix} new item(s) added")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
