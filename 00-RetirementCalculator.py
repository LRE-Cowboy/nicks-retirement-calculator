# Standard library imports
from typing import Dict, Any

# Third-party imports
import streamlit as st
from fpdf import FPDF
import plotly.graph_objs as go
import numpy as np
import pandas as pd

# Local imports
from inputs import get_user_inputs, validate_inputs
from calculations import project_retirement, monte_carlo_simulation
from outputs import (
	plot_net_worth_vs_time, plot_income_vs_expenses, 
	export_simulation_details, plot_income_vs_expenses_real
)
from utils import parse_savings_rates

st.title("Retirement Calculator")
st.markdown("""
Enter your details and assumptions below, then click **Run Simulation** to see your retirement projections.
""")

# Sidebar toggles for outputs
st.sidebar.header("Toggle Outputs")
show_net_worth_plot = st.sidebar.toggle("Net Worth vs Time Plot", value=True)
show_income_expense_plot = st.sidebar.toggle("Income vs Expenses Plot", value=True)
show_monte_carlo_results = st.sidebar.toggle("Monte Carlo Results", value=True)
show_salary_plot = st.sidebar.toggle("Salary vs Time Plot", value=True)

def adjust_savings_rates(variable_savings_rates: str, delta: float) -> str:
	"""
	Adjust all savings rates in the variable savings rates string by the delta amount.
	"""
	if not variable_savings_rates.strip():
		return ""
	
	rates = parse_savings_rates(variable_savings_rates)
	adjusted_rates = []
	
	for age, rate in rates:
		adjusted_rate = max(0, min(100, rate + delta))
		adjusted_rates.append(f"{age},{adjusted_rate}")
	
	return ";".join(adjusted_rates)

# Get user inputs
inputs = get_user_inputs()
is_valid, error_msg = validate_inputs(inputs)

if not is_valid:
	st.error(error_msg)
else:
	if st.button("Run Simulation"):
		# Run main projection
		projection = project_retirement(inputs)
		mc_results = monte_carlo_simulation(inputs)
		combined_results = {**projection, **mc_results}

		st.header("Simulation Results")
		# Calculate total inflation factor
		total_years = inputs["final_age"] - inputs["starting_age"]
		total_inflation_factor = (1 + inputs["inflation"] / 100) ** total_years
		current_dollar_worth = 1
		final_dollar_worth = total_inflation_factor
		
		st.markdown(f"""
		## Retirement Calculator Results
		**Key Metrics:**
		- **Retirement Age:** {projection['retirement_age']} years
		- **Years to Retirement:** {projection['years_to_retirement']} years
		- **Initial Withdrawal Rate:** {inputs['comfortable_withdrawal_rate']:.1f}%
		- **Average Withdrawal Rate:** {projection['avg_withdrawal_rate']:.2f}%
		- **Monte Carlo Success Rate:** {mc_results['success_rate']*100:.1f}%
		- **Total Inflation Impact:** ${current_dollar_worth:.2f} current = {final_dollar_worth:.2f} at age {inputs["final_age"]}
		""")

		# Display selected outputs
		if show_net_worth_plot:
			st.subheader("Net Worth vs Time")
			plot_net_worth_vs_time(projection)

		if show_income_expense_plot:
			st.subheader("Income and Expenses vs Time (Nominal Dollars)")
			plot_income_vs_expenses(projection)
			st.subheader("Income and Expenses vs Time (Current Day Dollars)")
			plot_income_vs_expenses_real(projection, inputs)

		if show_monte_carlo_results:
			st.subheader("Monte Carlo Simulation Results")
			st.markdown(f"""
			**Monte Carlo Simulation Results:**
			- **Success Rate:** {mc_results['success_rate']*100:.1f}%
			- **Median Net Worth at Death:** ${mc_results['median_net_worth']:,.0f}
			- **10th Percentile Net Worth at Death:** ${mc_results['percentile_10_net_worth']:,.0f}
			""")
			
			# Create histogram of net worths at death (nominal)
			fig = go.Figure()
			fig.add_trace(go.Histogram(x=mc_results['all_net_worths'], nbinsx=50, name="Net Worth Distribution (Nominal $)"))
			fig.update_layout(
				title="Distribution of Net Worth at Death (Monte Carlo, Nominal $)",
				xaxis_title="Net Worth at Death ($)",
				yaxis_title="Frequency"
			)
			st.plotly_chart(fig)
			
			# Create histogram of net worths at death (real/current $)
			final_age = inputs["final_age"]
			starting_age = inputs["starting_age"]
			inflation = inputs["inflation"] / 100
			inflation_factor = (1 + inflation) ** (final_age - starting_age)
			all_net_worths_real = [v / inflation_factor for v in mc_results['all_net_worths']]
			fig2 = go.Figure()
			fig2.add_trace(go.Histogram(x=all_net_worths_real, nbinsx=50, name="Net Worth Distribution (Real $)"))
			fig2.update_layout(
				title="Distribution of Net Worth at Death (Monte Carlo, Current Day $)",
				xaxis_title="Net Worth at Death (Current $)",
				yaxis_title="Frequency"
			)
			st.plotly_chart(fig2)
			
		# Always display savings return impact section
		st.subheader("Savings Rate Impact (+/- 1-5%)")
		deltas = [-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5]
		results = []
		for delta in deltas:
			test_inputs = inputs.copy()
			# Adjust both default savings rate and variable savings rates
			test_inputs["saving_rate"] = max(0, min(100, inputs["saving_rate"] + delta))
			test_inputs["variable_saving_rates"] = adjust_savings_rates(inputs["variable_saving_rates"], delta)
			proj = project_retirement(test_inputs)
			results.append({
				"Delta": f"{delta:+d}%",
				"Default Savings Rate": test_inputs["saving_rate"],
				"Retirement Age": proj["retirement_age"],
				"Final Net Worth": proj["net_worth"][-1]
			})
		df = pd.DataFrame(results)
		st.dataframe(df, hide_index=True, use_container_width=True)