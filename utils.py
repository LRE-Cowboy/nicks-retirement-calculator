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


def parse_savings_rates(s: str) -> List[Tuple[int, float]]:
	"""
	Parse savings rates from a string of the form '25,30;37,20.25'.
	Returns a list of (age, savings_rate) tuples.
	"""
	if not s.strip():
		return []
	rates = []
	for part in s.split(';'):
		try:
			age_str, rate_str = part.split(',')
			rates.append((int(age_str), float(rate_str)))
		except Exception:
			continue
	return rates


def get_savings_rate_at_age(age: int, savings_rates: List[Tuple[int, float]], default_rate: float) -> float:
	"""
	Get the savings rate for a given age from the list of savings rates.
	If no specific rate is set for the age, use the default rate.
	"""
	if not savings_rates:
		return default_rate
	
	# Sort rates by age to ensure we get the most recent applicable rate
	sorted_rates = sorted(savings_rates, key=lambda x: x[0])
	
	# Find the most recent rate that applies to this age or earlier
	applicable_rate = default_rate
	for rate_age, rate in sorted_rates:
		if rate_age <= age:
			applicable_rate = rate
		else:
			break
	
	return applicable_rate 