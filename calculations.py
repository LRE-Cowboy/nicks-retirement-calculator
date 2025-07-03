# Standard library imports
from typing import Dict, Any, Tuple, List

# Third-party imports
import numpy as np
import pandas as pd
from scipy.stats import norm

# Local imports
from utils import parse_salary_upgrades

# Constants
MonteCarloRuns = 2500


def project_retirement(inputs: Dict[str, Any]) -> Dict[str, Any]:
	"""
	Run deterministic projection of net worth, salary, and expenses over time.
	Returns a dictionary with time series data.
	"""
	ages = np.arange(inputs["starting_age"], inputs["final_age"] + 1)
	years = len(ages)
	
	# Initialize arrays
	income = np.zeros(years)
	salary = np.zeros(years)
	net_worth = np.zeros(years)
	expenses = np.zeros(years)
	
	# Parse salary upgrades
	salary_upgrades = parse_salary_upgrades(inputs["salary_upgrades"])
	upgrade_dict = {age: (upgrade_type, value) for age, upgrade_type, value in salary_upgrades}
	
	# Project salary over time
	current_salary = inputs["starting_salary"]
	for i, age in enumerate(ages):
		# Apply salary upgrades if any
		if age in upgrade_dict:
			upgrade_type, value = upgrade_dict[age]
			if upgrade_type.lower() == "raise":
				current_salary *= (1 + value / 100)
			elif upgrade_type.lower() == "absolute":
				current_salary = value
		# Apply annual raise (except for upgrade years)
		if age not in upgrade_dict and i > 0:
			current_salary *= (1 + inputs["raise_rate"] / 100)
		# Apply normalized salary cap (in current dollars, pre-retirement only)
		if i > 0 and (inputs.get("normalized_salary_cap", 0) > 0):
			# Compute inflation factor from starting_age to this year
			cumulative_inflation = (1 + inputs["inflation"] / 100) ** (age - inputs["starting_age"])
			nominal_cap = inputs["normalized_salary_cap"] * cumulative_inflation
			if current_salary > nominal_cap:
				current_salary = nominal_cap
		salary[i] = current_salary
		income[i] = salary[i]
	
	# Distribute extra expense across all retirement years (1/5th of the 5-year expense per year)
	annual_extra_expense = inputs["extra_expense"] / 5
	
	# Project net worth and expenses
	net_worth[0] = inputs["starting_fund"]
	financial_ready_age = None
	for i in range(1, years):
		age = ages[i]
		annual_savings = salary[i-1] * inputs["saving_rate"] / 100
		emergency_expense = salary[i-1] * inputs["emergency_fund"] / 100
		net_savings = annual_savings - emergency_expense
		net_worth[i] = net_worth[i-1] * (1 + inputs["savings_growth"] / 100) + net_savings
		expenses[i] = salary[i-1] - annual_savings
		# Check if portfolio can support the desired retirement spending using 4% rule
		# Calculate what the initial withdrawal would be at this portfolio value
		potential_initial_withdrawal = net_worth[i] * (inputs["comfortable_withdrawal_rate"] / 100)
		# Check if this withdrawal amount (in current dollars) can support the retirement spend
		if financial_ready_age is None and potential_initial_withdrawal >= inputs["retirement_spend"]:
			financial_ready_age = age
	
	# Determine retirement age based on selected mode
	retirement_mode = inputs.get("retirement_mode", "Extra Years of Work")
	if retirement_mode == "Minimum Retirement Age":
		min_retirement_age = inputs.get("min_retirement_age", inputs["starting_age"])
		if financial_ready_age is None:
			base_retirement_age = inputs["final_age"]
		else:
			base_retirement_age = max(financial_ready_age, min_retirement_age)
		retirement_age = base_retirement_age
	else:
		extra_years = inputs.get("extra_years_of_work", 0)
		if financial_ready_age is None:
			base_retirement_age = inputs["final_age"]
		else:
			base_retirement_age = max(financial_ready_age, inputs["starting_age"])
		retirement_age = min(base_retirement_age + extra_years, inputs["final_age"])
	
	# Now simulate year by year, switching to retirement at retirement_age
	retired = False
	for i in range(1, years):
		age = ages[i]
		if not retired and age >= retirement_age:
			retired = True
		force_retirement_age = age if retired and 'force_retirement_age' not in locals() else None
		if not retired:
			# Working years
			annual_savings = salary[i-1] * inputs["saving_rate"] / 100
			emergency_expense = salary[i-1] * inputs["emergency_fund"] / 100
			net_savings = annual_savings - emergency_expense
			net_worth[i] = net_worth[i-1] * (1 + inputs["savings_growth"] / 100) + net_savings
			expenses[i] = salary[i-1] - annual_savings
			income[i] = salary[i]
		else:
			# Retirement years - Implement 4% rule with adjustable withdrawal rate
			# Calculate years since retirement started
			years_since_retirement = age - retirement_age
			
			# Get the portfolio value at retirement (first retirement year)
			if years_since_retirement == 0:
				portfolio_at_retirement = net_worth[i-1]
				# Calculate initial withdrawal amount based on 4% rule
				# Use the comfortable_withdrawal_rate as the adjustable rate
				withdrawal_rate = inputs["comfortable_withdrawal_rate"] / 100
				initial_withdrawal = portfolio_at_retirement * withdrawal_rate
				# Store the initial withdrawal amount for inflation adjustments
				base_withdrawal_amount = initial_withdrawal
			
			# Apply inflation adjustment to the initial withdrawal amount
			inflation_factor = (1 + inputs["inflation"] / 100) ** years_since_retirement
			nominal_withdrawal = base_withdrawal_amount * inflation_factor
			
			# Add 1/5th of the 5-year extra expense to every year of retirement
			annual_extra_expense = inputs["extra_expense"] / 5
			extra_expense_inflated = annual_extra_expense * inflation_factor
			
			# Add emergency fund expenditure during retirement (using the same percentage as working years)
			# Use the nominal withdrawal as the "income" base for emergency fund calculation
			emergency_expense_retirement = nominal_withdrawal * inputs["emergency_fund"] / 100
			
			# Total expenses for this year
			expenses[i] = nominal_withdrawal + extra_expense_inflated + emergency_expense_retirement
			
			# Apply tax adjustment
			after_tax_expense = expenses[i] / (1 - inputs["retirement_tax"] / 100)
			
			# Update portfolio value
			net_worth[i] = net_worth[i-1] * (1 + inputs["retirement_growth"] / 100) - after_tax_expense
			income[i] = after_tax_expense  # Show the actual withdrawal amount needed (including taxes)
	
	# Calculate average withdrawal rate
	withdrawal_years = years - (retirement_age - inputs["starting_age"])
	if withdrawal_years > 0:
		total_withdrawal = sum(expenses[ages >= retirement_age])
		if net_worth[ages == retirement_age][0] > 0:
			avg_withdrawal_rate = (total_withdrawal / withdrawal_years) / net_worth[ages == retirement_age][0] * 100
		else:
			avg_withdrawal_rate = 0
	else:
		avg_withdrawal_rate = 0
	
	return {
		"ages": ages,
		"net_worth": net_worth,
		"income": income,
		"expenses": expenses,
		"retirement_age": retirement_age,
		"years_to_retirement": retirement_age - inputs["starting_age"],
		"avg_withdrawal_rate": avg_withdrawal_rate
	}


def monte_carlo_simulation(inputs: Dict[str, Any], runs: int = MonteCarloRuns) -> Dict[str, Any]:
	"""
	Run Monte Carlo simulation for retirement success rate and net worth at death.
	Returns a dictionary with simulation results.
	"""
	net_worths_at_death = []
	success_count = 0
	
	for _ in range(runs):
		# Add random variation to key parameters
		savings_growth_variation = np.random.normal(inputs["savings_growth"], inputs["savings_growth"] * 0.1)
		retirement_growth_variation = np.random.normal(inputs["retirement_growth"], inputs["retirement_growth"] * 0.1)
		inflation_variation = np.random.normal(inputs["inflation"], inputs["inflation"] * 0.05)
		
		# Create modified inputs
		modified_inputs = inputs.copy()
		modified_inputs["savings_growth"] = savings_growth_variation
		modified_inputs["retirement_growth"] = retirement_growth_variation
		modified_inputs["inflation"] = inflation_variation
		
		# Run projection
		projection = project_retirement(modified_inputs)
		
		# Check if successful (net worth never goes negative)
		if np.all(projection["net_worth"] >= 0):
			success_count += 1
		
		net_worths_at_death.append(projection["net_worth"][-1])
	
	success_rate = success_count / runs
	median_net_worth = np.median(net_worths_at_death)
	percentile_10_net_worth = np.percentile(net_worths_at_death, 10)
	
	return {
		"success_rate": success_rate,
		"median_net_worth": median_net_worth,
		"percentile_10_net_worth": percentile_10_net_worth,
		"all_net_worths": net_worths_at_death
	}


def sensitivity_analysis(inputs: Dict[str, Any], variable: str, delta: float) -> Dict[str, Any]:
	"""
	Return projection results with the specified variable changed by delta.
	"""
	inputs_mod = inputs.copy()
	inputs_mod[variable] += delta
	return project_retirement(inputs_mod) 