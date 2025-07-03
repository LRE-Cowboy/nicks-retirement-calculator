# Standard library imports
from typing import Dict, Any

# Third-party imports
import streamlit as st
from fpdf import FPDF
import plotly.graph_objs as go
import numpy as np

# Local imports
from inputs import get_user_inputs, validate_inputs
from calculations import project_retirement, monte_carlo_simulation, sensitivity_analysis
from outputs import (
	plot_net_worth_vs_time, plot_income_vs_expenses, 
	export_simulation_details, plot_income_vs_expenses_real
)

def export_outputs_to_pdf(inputs, projection, mc_results, filename="simulation_results.pdf"):
	pdf = FPDF()
	pdf.add_page()
	pdf.set_font("Times", size=12)
	pdf.cell(200, 10, txt="Retirement Calculator Simulation Results", ln=True, align="C")
	pdf.ln(5)
	pdf.set_font("Times", size=11)
	pdf.cell(0, 10, txt="Key Metrics:", ln=True)
	pdf.cell(0, 10, txt=f"Retirement Age: {projection['retirement_age']} years", ln=True)
	pdf.cell(0, 10, txt=f"Years to Retirement: {projection['years_to_retirement']} years", ln=True)
	pdf.cell(0, 10, txt=f"Average Withdrawal Rate: {projection['avg_withdrawal_rate']:.2f}%", ln=True)
	pdf.cell(0, 10, txt=f"Monte Carlo Success Rate: {mc_results['success_rate']*100:.1f}%", ln=True)
	pdf.ln(5)
	pdf.cell(0, 10, txt="Monte Carlo Simulation Results:", ln=True)
	pdf.cell(0, 10, txt=f"Success Rate: {mc_results['success_rate']*100:.1f}%", ln=True)
	pdf.cell(0, 10, txt=f"Median Net Worth at Death: ${mc_results['median_net_worth']:,.0f}", ln=True)
	pdf.cell(0, 10, txt=f"10th Percentile Net Worth at Death: ${mc_results['percentile_10_net_worth']:,.0f}", ln=True)
	pdf.ln(5)
	pdf.cell(0, 10, txt="NOTES:", ln=True)
	pdf.cell(0, 10, txt="- This simulation assumes no social security or pension income", ln=True)
	pdf.cell(0, 10, txt="- All amounts are in current dollars", ln=True)
	pdf.cell(0, 10, txt="- Monte Carlo simulation includes random variations in growth rates and inflation", ln=True)
	pdf.output(filename)

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
show_savings_return_impact = st.sidebar.toggle("Savings Return Impact", value=True)
show_sensitivity_analysis = st.sidebar.toggle("Sensitivity Analysis", value=True)

# Sensitivity analysis controls
sensitivity_variable = st.sidebar.selectbox(
	"Variable to Test (Sensitivity)",
	["inflation", "savings_growth", "saving_rate", "raise_rate", "retirement_spend"],
	index=0
)
sensitivity_delta = st.sidebar.slider("Change Amount (Sensitivity)", min_value=-10.0, max_value=10.0, value=1.0, step=0.5)

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
			
			if st.button("Export Outputs to PDF"):
				export_outputs_to_pdf(inputs, projection, mc_results)
				st.success("Outputs exported to simulation_results.pdf")

		if show_savings_return_impact:
			st.subheader("Savings Return Rate Impact")
			# display_varied_return_rate_impact(inputs, "savings")

		if show_sensitivity_analysis:
			st.subheader("Sensitivity Analysis")
			st.markdown("**Test how changes in assumptions affect your retirement plan:**")
			if st.button("Run Sensitivity Test"):
				sensitivity_results = sensitivity_analysis(inputs, sensitivity_variable, sensitivity_delta)
				st.markdown(f"""
				**Sensitivity Analysis Results:**
				**Base Case:**
				- Retirement Age: {projection['retirement_age']} years
				- Success Rate: {mc_results['success_rate']*100:.1f}%
				**With {sensitivity_variable} changed by {sensitivity_delta:+.1f}:**
				- Retirement Age: {sensitivity_results['retirement_age']} years
				- Change: {sensitivity_results['retirement_age'] - projection['retirement_age']:+.0f} years
				""")

		if st.button("Export Simulation Details"):
			export_simulation_details(inputs, combined_results)
			st.success("Simulation exported to simulation_export.txt")