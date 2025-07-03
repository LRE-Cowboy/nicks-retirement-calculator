# Standard library imports
from typing import List, Tuple, Dict, Any

# Third-party imports
import streamlit as st
import numpy as np
import pandas as pd

# Local imports
from utils import parse_salary_upgrades

# Constants for tooltips and descriptions
StartingAgeTooltip = "Your current age in years."
StartingFundTooltip = "Total current investable assets ($)."
StartingSalaryTooltip = "Your current annual salary, including bonuses and stock vesting ($)."
SavingRateTooltip = "Percent of salary saved each year (%)."
TaxAdvantagedTooltip = "Percent of savings going to tax-advantaged accounts (e.g., 401k, Roth)."
RaiseRateTooltip = "Expected average annual raise rate (%)."
EmergencyFundTooltip = "Annual emergency fund expenditure as a percent of income during working years, and as a percent of retirement withdrawals during retirement (%)."
SalaryUpgradesTooltip = "Expected salary upgrades in format: 'age,type,value;age,type,value'. Types: 'raise' (percentage) or 'absolute' (dollar amount). Example: '30,raise,10;35,absolute,150000'"
SavingsGrowthTooltip = "Expected annual growth rate of savings before retirement (%)."
RetirementGrowthTooltip = "Expected annual growth rate of investments during retirement (%)."
RetirementSpendTooltip = "Target annual spending in retirement (current dollars). This is the amount you want to spend each year in retirement, adjusted for inflation over time."
ExtraExpenseTooltip = "Extra 5-year retirement expense distributed evenly across all retirement years (e.g., travel, home repairs) ($)."
RetirementTaxTooltip = "Estimated average tax rate during retirement (%)."
FinalAgeTooltip = "Expected age at death."
InflationTooltip = "Average annual inflation rate (%)."
ComfortableWithdrawalTooltip = "The 4% rule withdrawal rate (e.g., 3-4%) used for retirement spending. This percentage of your portfolio at retirement will be withdrawn initially, then adjusted for inflation each year. The 4% rule is designed to last ~30 years, while 3% is more conservative and lasts ~40+ years. When your portfolio value * this rate equals your annual retirement spend, you are considered able to retire."
ExtraYearsOfWorkTooltip = "Number of years you plan to work past the minimum retirement age (after you could afford to retire)."
MinRetirementAgeTooltip = "The minimum age at which retirement will be considered, regardless of financial readiness. Enable this to set a minimum retirement age."
NormalizedSalaryCapTooltip = "Maximum allowed pre-retirement salary/income in current dollars (inflation-adjusted). Your salary, when normalized to current dollars, will not exceed this cap before retirement."


def get_user_inputs() -> Dict[str, Any]:
	"""
	Render Streamlit input widgets and return a dictionary of user inputs.
	"""
	st.header("Retirement Calculator Inputs")
	st.subheader("Basic Information")
	starting_age = st.number_input("Starting Age", min_value=18, max_value=70, value=23, help=StartingAgeTooltip)
	starting_fund = st.number_input("Starting Fund ($)", min_value=0, max_value=1_000_000, value=50000, step=1000, help=StartingFundTooltip)
	starting_salary = st.number_input("Starting Salary ($)", min_value=0, max_value=1_000_000, value=100000, step=1000, help=StartingSalaryTooltip)
	normalized_salary_cap = st.number_input("Normalized Salary Cap ($, current dollars)", min_value=0, max_value=1_000_000, value=0, step=1000, help=NormalizedSalaryCapTooltip)
	# Segmented control for retirement mode
	retirement_mode = st.segmented_control(
		"Retirement Timing Mode",
		["Extra Years of Work", "Minimum Retirement Age"],
		default="Extra Years of Work",
		help="Choose how to determine your actual retirement age: by working extra years after you could retire, or by setting a minimum retirement age."
	)
	extra_years_of_work = 0
	min_retirement_age = None
	if retirement_mode == "Extra Years of Work":
		extra_years_of_work = st.number_input("Extra Years of Work", min_value=0, max_value=50, value=0, step=1, help=ExtraYearsOfWorkTooltip)
	elif retirement_mode == "Minimum Retirement Age":
		min_retirement_age = st.number_input("Minimum Retirement Age", min_value=starting_age, max_value=120, value=starting_age, help=MinRetirementAgeTooltip)
	
	st.subheader("Savings & Investment")
	saving_rate = st.number_input("Saving Rate (%)", min_value=0.0, max_value=100.0, value=25.0, step=0.1, help=SavingRateTooltip)
	savings_growth = st.number_input("Savings Stock Growth Rate (%)", min_value=-10.0, max_value=20.0, value=7.0, step=0.1, help=SavingsGrowthTooltip)
	retirement_growth = st.number_input("Retirement Stock Growth Rate (%)", min_value=-10.0, max_value=20.0, value=5.0, step=0.1, help=RetirementGrowthTooltip)
	comfortable_withdrawal_rate = st.number_input("Comfortable Withdrawal Rate (%)", min_value=2.0, max_value=10.0, value=3.0, step=0.1, help=ComfortableWithdrawalTooltip)
	
	st.subheader("Income Growth")
	raise_rate = st.number_input("Raise Rate (%)", min_value=0.0, max_value=20.0, value=3.0, step=0.1, help=RaiseRateTooltip)
	emergency_fund = st.number_input("Emergency Fund Expenditure (% of income)", min_value=0.0, max_value=50.0, value=2.5, step=0.1, help=EmergencyFundTooltip)
	salary_upgrades = st.text_input(
		"Salary Upgrades",
		value="",
		help=(
			"Expected salary upgrades in format: 'age,type,value;age,type,value'. "
			"Types: 'raise' (percentage) or 'absolute' (dollar amount). "
			"Example: '30,raise,10;35,absolute,150000'. "
			"Use a semicolon to separate upgrades. For a 10% raise at age 30: '30,raise,10'. "
			"For a salary jump to $150,000 at age 35: '35,absolute,150000'. "
			"(No $ or % symbols, just numbers.)"
		)
	)
	
	st.subheader("Retirement Planning")
	retirement_spend = st.number_input("Estimated Retirement Spend ($)", min_value=0, max_value=500_000, value=60000, step=1000, help=RetirementSpendTooltip)
	extra_expense = st.number_input("5-Year Retirement 'Extra' Expense ($)", min_value=0, max_value=500_000, value=5000, step=1000, help=ExtraExpenseTooltip)
	retirement_tax = st.number_input("Estimated Retirement Tax Rate (%)", min_value=0.0, max_value=50.0, value=9.0, step=0.1, help=RetirementTaxTooltip)
	
	st.subheader("Assumptions")
	final_age = st.number_input("Final Age (Death)", min_value=60, max_value=120, value=90, help=FinalAgeTooltip)
	inflation = st.number_input("Average Inflation Rate (%)", min_value=0.0, max_value=10.0, value=2.0, step=0.1, help=InflationTooltip)

	inputs = {
		"starting_age": starting_age,
		"starting_fund": starting_fund,
		"starting_salary": starting_salary,
		"normalized_salary_cap": normalized_salary_cap,
		"retirement_mode": retirement_mode,
		"extra_years_of_work": extra_years_of_work,
		"min_retirement_age": min_retirement_age,
		"saving_rate": saving_rate,
		"savings_growth": savings_growth,
		"retirement_growth": retirement_growth,
		"comfortable_withdrawal_rate": comfortable_withdrawal_rate,
		"raise_rate": raise_rate,
		"emergency_fund": emergency_fund,
		"salary_upgrades": salary_upgrades,
		"retirement_spend": retirement_spend,
		"extra_expense": extra_expense,
		"retirement_tax": retirement_tax,
		"final_age": final_age,
		"inflation": inflation
	}
	return inputs


def validate_inputs(inputs: Dict[str, Any]) -> Tuple[bool, str]:
	"""
	Validate user inputs for logical consistency.
	Returns (is_valid, error_message).
	"""
	# Basic age validation
	if inputs["starting_age"] >= inputs["final_age"]:
		return False, "Starting age must be less than final age."
	
	# Rate validations
	if inputs["saving_rate"] < 0 or inputs["saving_rate"] > 100:
		return False, "Saving rate must be between 0 and 100%."
	
	if inputs["raise_rate"] < 0:
		return False, "Raise rate must be non-negative."
	
	if inputs["savings_growth"] < -10 or inputs["savings_growth"] > 20:
		return False, "Savings growth rate out of plausible range (-10% to 20%)."
	
	if inputs["retirement_growth"] < -10 or inputs["retirement_growth"] > 20:
		return False, "Retirement growth rate out of plausible range (-10% to 20%)."
	
	if inputs["retirement_tax"] < 0 or inputs["retirement_tax"] > 50:
		return False, "Retirement tax rate must be between 0 and 50%."
	
	if inputs["inflation"] < 0 or inputs["inflation"] > 10:
		return False, "Inflation rate must be between 0 and 10%."
	
	if inputs["emergency_fund"] < 0 or inputs["emergency_fund"] > 50:
		return False, "Emergency fund expenditure must be between 0 and 50% of income."
	
	# Validate salary upgrades format
	if inputs["salary_upgrades"].strip():
		try:
			upgrades = parse_salary_upgrades(inputs["salary_upgrades"])
			for age, upgrade_type, value in upgrades:
				if age < inputs["starting_age"] or age > inputs["final_age"]:
					return False, f"Salary upgrade age {age} must be between starting age and final age."
				if upgrade_type.lower() not in ["raise", "absolute"]:
					return False, f"Salary upgrade type '{upgrade_type}' must be 'raise' or 'absolute'."
				if value <= 0:
					return False, f"Salary upgrade value must be positive."
		except Exception as e:
			return False, f"Invalid salary upgrades format. Use: 'age,type,value;age,type,value'. Error: {str(e)}"
	
	# Logical consistency checks
	if inputs["retirement_spend"] <= 0:
		return False, "Retirement spend must be positive."
	
	if inputs["starting_fund"] < 0:
		return False, "Starting fund cannot be negative."
	
	if inputs["starting_salary"] <= 0:
		return False, "Starting salary must be positive."
	
	return True, "" 