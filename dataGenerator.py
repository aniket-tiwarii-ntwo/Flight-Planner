import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass

# default base date if not provided
DEFAULT_BASE_DATE = datetime.now()

@dataclass
class EntitySpan:
    start: int
    end: int
    label: str

    def to_list(self):
        return [self.start, self.end, self.label]


class FlightNERGenerator:
    def __init__(self, out_dir: str = ".", base_date: datetime = DEFAULT_BASE_DATE, seed: Optional[int] = None):
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)

        self.base_date = base_date

        self.seed = seed
        if seed is not None:
            random.seed(seed)

        # more Cities can be added later
        self.CITIES = [
            "New York", "Los Angeles", "Paris", "London", "Tokyo", "Dubai", "Singapore",
            "Sydney", "Boston", "Madrid", "Mumbai", "Delhi", "Bangalore", "San Francisco","Chicago", "Toronto", "Rome", "Barcelona", "Berlin", "Hong Kong", "Seoul","Bangkok", "Istanbul", "Melbourne", "Jakarta", "Kuala Lumpur", "Cairo", "Doha","San Diego", "Seattle", "Washington D.C.", "Vancouver", "Mexico City", "Buenos Aires", "Lima", "Santiago", "Johannesburg", "Cape Town", "Athens"
        ]
        # more AirLines can be added later
        self.AIRLINES = [
            "Emirates", "Qatar Airways", "Singapore Airlines", "Delta", "Qantas", "Lufthansa",
            "British Airways", "Air India", "Cathay Pacific", "Japan Airlines", "ANA", "Etihad", "KLM"
        ]
        self.TRAVEL_CLASSES = ["economy", "premium economy", "business", "first class"]

        # Currently only one-way supported ---> will add round-trip later, when the templates are ready
        self.TRIP_TYPES = ["one-way"]

        # Time phrases  ----> I add possible variations to avoid template rigidity
        self.DEPARTURE_TIME_PHRASES = ["departing", "leaving", "take off", "depart"]
        self.ARRIVAL_TIME_PHRASES = ["arriving", "arrive", "landing", "get in"]
        self.TIME_EXPRESSIONS = ["after 6pm", "before 12pm", "between 12pm - 6pm", "between 6am - 12pm", "6:30 AM", "09:00", "evening", "night"]

        self.CURRENCY_SYMBOLS = {"USD": "$", "INR": "₹", "EUR": "€", "GBP": "£", "JPY": "¥"}
        self.CURRENCY_CODES = list(self.CURRENCY_SYMBOLS.keys())

        # Verbs used in text only (not annotated)  ----> this I do add little randomness to avoid template rigidity
        self.VERBS = ["Show me", "Find", "Search for", "Looking for", "Can you find", "Need", "Book", "I want"]
        self.COLLOQUIAL_VERBS = ["Wanna", "Gimme", "Got me", "Looking to get"]

        # List of entity templates
        self.TEMPLATES = [
            ["Show me flights from ", {"ent": "SOURCE"}, " to ", {"ent": "DESTINATION"}, " on ", {"ent": "DEPART_DATE"}, "."],
            ["I want a ", {"ent": "TRIP_TYPE"}, " flight from ", {"ent": "SOURCE"}, " to ", {"ent": "DESTINATION"}, " on ", {"ent": "DEPART_DATE"}, "."],
            ["Find flights from ", {"ent": "SOURCE"}, " to ", {"ent": "DESTINATION"}, " on ", {"ent": "DEPART_DATE"}, " for ", {"ent": "ADULTS"}, " adults and ", {"ent": "CHILDREN"}, " children", "."],
            [{"ent": "VERB_START"}, " ", {"ent": "TRAVEL_CLASS"}, " flights from ", {"ent": "SOURCE"}, " to ", {"ent": "DESTINATION"}, " on ", {"ent": "DEPART_DATE"}, "."],
            [{"ent": "VERB_START"}, " flights from ", {"ent": "SOURCE"}, " to ", {"ent": "DESTINATION"}, " on ", {"ent": "DEPART_DATE"}, " departing ", {"ent": "DEPARTURE_TIME"}, "."],
            [{"ent": "VERB_START"}, " flights from ", {"ent": "SOURCE"}, " to ", {"ent": "DESTINATION"}, " on ", {"ent": "DEPART_DATE"}, " arriving ", {"ent": "ARRIVAL_TIME"}, "."],
            [{"ent": "VERB_START"}, " flights from ", {"ent": "SOURCE"}, " to ", {"ent": "DESTINATION"}, " on ", {"ent": "DEPART_DATE"}, " with ", {"ent": "STOPS"}, " stop(s) and price under ", {"ent": "PRICE"}, "."],
            ["Are there flights from ", {"ent": "SOURCE"}, " to ", {"ent": "DESTINATION"}, " on ", {"ent": "DEPART_DATE"}, " operated by ", {"ent": "AIRLINE"}, "?"],
            ["Search for a ", {"ent": "TRIP_TYPE"}, " ", {"ent": "TRAVEL_CLASS"}, " flight from ", {"ent": "SOURCE"}, " to ", {"ent": "DESTINATION"}, " on ", {"ent": "DEPART_DATE"}, " for ", {"ent": "ADULTS"}, " adults, ", {"ent": "CHILDREN"}, " children, and ", {"ent": "INFANTS"}, " infants, with ", {"ent": "STOPS"}, " stop(s)."]
        ]

        # optional entities (safe to skip if you want sparser utterances)
        self.optional_entities = {"TRIP_TYPE", "ADULTS", "CHILDREN", "INFANTS", "TRAVEL_CLASS", "STOPS", "DEPARTURE_TIME", "ARRIVAL_TIME", "AIRLINE", "PRICE"}

    # ---- helper methods ----
    def ordinal(self, n: int) -> str:
        return "%d%s" % (n, "th" if 11 <= n % 100 <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th"))

    def random_future_date(self, days_range: int = 360) -> datetime:
        return self.base_date + timedelta(days=random.randint(1, days_range))

    def format_date_variations(self, dt: datetime) -> str:
        """
        Return a single, human-friendly date string chosen randomly from
        several styles. Does NOT return any metadata (only the visible date).
        Avoids adding prefixes like 'on' because templates already include them.
        """
        choices = []

        # canonical / structured formats
        choices.append(dt.strftime("%Y-%m-%d"))           # ISO
        choices.append(dt.strftime("%d %B %Y"))           # 01 January 2025
        choices.append(f"{self.ordinal(dt.day)} {dt.strftime('%B')} {dt.year}")  # 1st January 2025
        choices.append(dt.strftime("%b %d, %Y"))          # Jan 01, 2025
        choices.append(dt.strftime("%b %d"))              # Jan 01
        choices.append(dt.strftime("%m/%d/%Y"))           # 01/01/2025
        choices.append(dt.strftime("%d/%m/%Y"))           # 01/01/2025 (alt)
        choices.append(dt.strftime("%A, %d %B %Y"))       # Monday, 01 January 2025

        # relative / conversational options (only when they make sense)
        days_diff = (dt - self.base_date).days
        if days_diff == 0:
            choices.append("today")
        if days_diff == 1:
            choices.append("tomorrow")
        if 0 <= days_diff <= 6:
            choices.append(f"this {dt.strftime('%A')}")
            choices.append(f"on {dt.strftime('%A')}")   # e.g. on Monday
        if 1 <= days_diff <= 14:
            choices.append(f"next {dt.strftime('%A')}")
        if 1 <= days_diff <= 90:
            choices.append(f"in {days_diff} days")

        # final selection
        return random.choice(choices)

    def format_price(self) -> str:
        """
        Return only a textual representation of a price (no meta).
        Examples: "$500", "500 USD", "under 500 USD", "less than ₹3000"

        "symbol" → $500, ₹3000, ¥25000
        "code" → 500 USD, 3000 INR, 25000 JPY
        "words" → "under 500 USD", "under 25000 JPY"
        "plain" → "less than ₹3000" or "under $500"
        """
        currency = random.choice(self.CURRENCY_CODES)

        symbol = self.CURRENCY_SYMBOLS[currency]

        if currency == "INR":
            amount = random.randint(0, 300000)
        elif currency == "JPY":
            amount = random.randint(0, 300000)
        else:
            amount = random.randint(0, 300000)
        style = random.choice(["symbol", "code", "words", "plain"])

        if style == "symbol":
            text = f"{symbol}{amount}"
        elif style == "code":
            text = f"{amount} {currency}"
        elif style == "words":
            text = f"under {amount} {currency}"
        else:
            # plain textual variant; try to keep it natural
            text = f"less than {symbol}{amount}" if random.random() < 0.5 else f"under {symbol}{amount}"
        return text

    def format_time_expression(self, kind: str = "depart") -> str:

        """
        80% chance: "prefix expr" → "leaving tomorrow morning"
        20% chance: "expr prefix" → "tomorrow morning leaving"
        """
        expr = random.choice(self.TIME_EXPRESSIONS)
        prefix = random.choice(self.DEPARTURE_TIME_PHRASES if kind == "depart" else self.ARRIVAL_TIME_PHRASES)
        return f"{prefix} {expr}" if random.random() < 0.8 else f"{expr} {prefix}"

    def choose_two_distinct_cities(self) -> Tuple[str, str]:
        a, b = random.sample(self.CITIES, 2)
        return a, b

    def gen_entity(self, ent: str, src: Optional[str] = None) -> Dict[str, Any]:
        """
        Return only {"text": <string>} for each entity
        """
        if ent == "SOURCE":
            return {"text": random.choice(self.CITIES)}
        if ent == "DESTINATION":
            pool = [c for c in self.CITIES if c != src] if src else self.CITIES
            return {"text": random.choice(pool)}
        if ent == "DEPART_DATE":
            dt = self.random_future_date()
            text = self.format_date_variations(dt)
            return {"text": text}
        if ent == "TRIP_TYPE":
            return {"text": random.choice(self.TRIP_TYPES)}
        if ent == "ADULTS":
            return {"text": str(random.randint(1, 4))}
        if ent == "CHILDREN":
            return {"text": str(random.choices([0, 0, 1, 2, 3], weights=[1, 2, 6, 3, 1])[0])}
        if ent == "INFANTS":
            return {"text": str(random.choices([0, 0, 0, 1, 1], weights=[3, 3, 2, 1, 1])[0])}
        if ent == "TRAVEL_CLASS":
            return {"text": random.choice(self.TRAVEL_CLASSES)}
        if ent == "DEPARTURE_TIME":
            return {"text": self.format_time_expression('depart')}
        if ent == "ARRIVAL_TIME":
            return {"text": self.format_time_expression('arrive')}
        if ent == "STOPS":
            return {"text": str(random.choice([0, 0, 0, 1, 1, 2]))}
        if ent == "PRICE":
            # Now returns only text (no meta)
            text = self.format_price()
            return {"text": text}
        if ent == "AIRLINE":
            return {"text": random.choice(self.AIRLINES)}
        if ent == "VERB_START":
            return {"text": random.choice(self.VERBS)}
        if ent == "COLLOQ_VERB":
            return {"text": random.choice(self.COLLOQUIAL_VERBS)}
        return {"text": "UNK"}

    # Core renderer (span-safe)
    def render_from_pattern(self, pattern: List[Any], allow_partial: bool = True) -> Dict[str, Any]:
        text = ""
        entities: List[EntitySpan] = []

        # pre-select src/dst if pattern includes both
        has_src = any(isinstance(tok, dict) and tok["ent"] == "SOURCE" for tok in pattern)
        has_dst = any(isinstance(tok, dict) and tok["ent"] == "DESTINATION" for tok in pattern)
        src_val, dst_val = (None, None)
        if has_src and has_dst:
            src_val, dst_val = self.choose_two_distinct_cities()

        for tok in pattern:
            if isinstance(tok, str):
                text += tok
                continue

            if isinstance(tok, dict):
                ent = tok["ent"]

                # verb / colloquial verb handled by gen_entity now
                if ent in {"VERB_START", "COLLOQ_VERB"}:
                    val_text = self.gen_entity(ent)["text"]
                    start = len(text)
                    text += val_text
                    end = len(text)
                    # these are not typically annotated in your templates, but if you want to annotate,
                    # keep the ent name; here we skip adding spans for verbs to mimic original behaviour
                    continue

                if ent == "SOURCE":
                    val_text = src_val if src_val else self.gen_entity("SOURCE")["text"]
                elif ent == "DESTINATION":
                    val_text = dst_val if dst_val else self.gen_entity("DESTINATION", src=src_val)["text"]
                else:
                    val_text = self.gen_entity(ent, src=src_val)["text"]

                start = len(text)
                text += val_text
                end = len(text)
                entities.append(EntitySpan(start, end, ent))

        return {"text": text, "entities": [e.to_list() for e in entities]}

    # Generation + saving
    def generate(self, n: int = 1000) -> List[Dict[str, Any]]:
        examples = []
        for _ in range(n):
            pattern = random.choice(self.TEMPLATES)
            ex = self.render_from_pattern(pattern)
            examples.append(ex)
        return examples

    def save_json(self, examples: List[Dict[str, Any]], filename: Path) -> None:
        out_path = self.out_dir / filename
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(examples, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    generator = FlightNERGenerator(out_dir=".", seed=123)
    data = generator.generate(n=5000)
    generator.save_json(data, filename="data/flight_spacy_dataset.json")