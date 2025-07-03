# Standard library imports
from typing import List, Tuple


def parse_salary_upgrades(s: str) -> List[Tuple[int, str, float]]:
	"""
	Parse salary upgrades from a string of the form '30,raise,125000;35,raise,150000'.
	Returns a list of (age, type, value) tuples.
	"""
	if not s.strip():
		return []
	upgrades = []
	for part in s.split(';'):
		try:
			age_str, type_str, value_str = part.split(',')
			upgrades.append((int(age_str), type_str.strip(), float(value_str)))
		except Exception:
			continue
	return upgrades 