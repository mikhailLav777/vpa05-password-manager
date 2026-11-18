"""Общие правила генерации для окна и терминала."""

import string
from dataclasses import dataclass
from secrets import SystemRandom


AMBIGUOUS = frozenset("0O1Il")
DEFAULT_SPECIALS = "!@#$%&*+-_"
MAX_LENGTH = 64
MAX_COUNT = 20


@dataclass(frozen=True)
class PasswordGenerator:
    length: int = 16
    uppercase: bool = True
    lowercase: bool = True
    digits: bool = True
    specials: bool = True
    exclude_ambiguous: bool = True
    special_chars: str = DEFAULT_SPECIALS

    def generate(self, count: int = 1) -> list[str]:
        if not 1 <= self.length <= MAX_LENGTH:
            raise ValueError(f"Длина должна быть от 1 до {MAX_LENGTH} символов.")
        if not 1 <= count <= MAX_COUNT:
            raise ValueError(f"Количество должно быть от 1 до {MAX_COUNT}.")
        if self.specials:
            if not self.special_chars or any(char not in string.punctuation for char in self.special_chars):
                raise ValueError("Укажи хотя бы один спецсимвол. Например, !_-.")

        groups = [
            "".join(dict.fromkeys(char for char in group if not self.exclude_ambiguous or char not in AMBIGUOUS))
            for enabled, group in (
                (self.uppercase, string.ascii_uppercase),
                (self.lowercase, string.ascii_lowercase),
                (self.digits, string.digits),
                (self.specials, self.special_chars),
            )
            if enabled
        ]
        if not groups:
            raise ValueError("Включи хотя бы одну группу символов.")
        if self.length < len(groups):
            raise ValueError(f"Для выбранных групп нужна длина не меньше {len(groups)}.")

        alphabet = "".join(groups)
        rng = SystemRandom()
        passwords = []
        for _ in range(count):
            characters = [rng.choice(group) for group in groups]
            characters.extend(rng.choice(alphabet) for _ in range(self.length - len(groups)))
            rng.shuffle(characters)
            passwords.append("".join(characters))
        return passwords
