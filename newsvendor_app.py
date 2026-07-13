import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from scipy.stats import norm

#title
st.set_page_config(
    page_title="The Newsvendor Problem",layout="centered",
)

#parameters
P = 1.00 #sell price
C = 0.50 #purchase cost
S = 0.05 #salvage
mean = 100
std = 20 
days = 7

over = C-S
under = P-C
c_ratio = under/(under+over)
Qs = (norm.ppf(c_ratio, mean, std))

# ── Session state init ─────────────────────────────────────────────────────────
def init_state():
    if "day" not in st.session_state:
        st.session_state.day        = 1
        st.session_state.history    = []   
        st.session_state.phase      = "order"   
        st.session_state.order_qty  = 100
        st.session_state.demand_today = None
        np.random.seed()   

init_state()

def compute_profit(order, demand):
    sold = min(order, demand)
    left = max(0, order-demand)
    short = max(0, demand-order)
    rev = sold*P
    salvage = left*S
    cost = order*C
    profit = rev+salvage-cost
    return profit, sold, left, short

def running_total():
    return sum(r["profit"] for r in st.session_state.history)

def reset_game():
    for key in ["day","history","phase","order_qty","demand_today"]:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

st.markdown("# The Newsvendor Problem")
st.markdown("*Run a news stand for a week. Compare your results to optimal results at the end.*")

#sidebar showing known values
with st.sidebar:
    st.markdown("## Known Values")
    st.markdown(f"""
| Argument | Value |
|------|-------|
| Selling price | $1.00 / paper |
| Purchase cost | $0.50 / paper |
| Salvage value | $0.05 / paper |
| Average daily demand  | 100 papers/day |
| Standard deviation | 20 papers/day |
""")
    st.divider()
    if st.session_state.phase != "done":
        total = running_total()
        st.metric("Running Total", f'${total:,.2f}')
    st.divider()
    if st.button("Restart Game"):
        reset_game()

# ── DONE SCREEN ────────────────────────────────────────────────────────────────
if st.session_state.phase == "done":
    total = running_total()
    hist_df = pd.DataFrame(st.session_state.history)

    # with optimal for comparison
    opt_prof = []
    for row in st.session_state.history:
        p, *_ = compute_profit(Qs, row["demand"])
        opt_prof.append(p)
    opt_total = sum(opt_prof)

    st.markdown("## Week Complete!")
    st.divider()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('### Your Total Profit')
        st.metric("", f'${total:,.2f}')
    with col2:
        st.markdown('### Optimal Q* ')
        st.metric("", f"${opt_total:,.2f}")
    with col3:
        gap = total - opt_total
        g_color = "green" if gap >= 0 else "red"
        st.markdown('### Difference')
        if gap >= 0:
            st.success(f'**+${gap:.2f}**')
        else:
            st.error(f'**${gap:.2f}**')
    st.divider()


###    #scatter of demand vs order
    fig2 = go.Figure()
    fig2.add_scatter(
        x=[f"Day {r['day']}" for r in st.session_state.history],
        y=[r["order"] for r in st.session_state.history],
        mode="lines+markers", name="Your Order",
        line=dict(color="#9467bd"), marker=dict(size=8, symbol="square")
    )

    fig2.update_layout(
        title="Your Orders vs. Realized Demand",
        yaxis_title="Papers", xaxis_title="",
        legend=dict(orientation="h", y=1.12),
        plot_bgcolor="white", height=300
    )
    fig2.update_yaxes(gridcolor="#eee")
    st.plotly_chart(fig2, use_container_width=True)

    # summary table
    st.markdown("### Summary")
    display_df = pd.DataFrame([{
        "Day": r["day"],
        "Ordered": r["order"],
        "Demand": r["demand"],
        "Sold": r["sold"],
        "Leftover": r["leftover"],
        "Shortage": r["shortage"],
        "Profit": f"${r['profit']:.2f}"
    } for r in st.session_state.history])
    st.dataframe(display_df)


    # Monte Carlo simulation test
    qs = range(0,200,1)
    mc_profits = []
    for q in qs:
        demand = np.random.normal(mean,std,1000000).clip(0)
        profit = np.minimum(demand,q)*P + np.maximum(0,q-demand)*S-q*C
        mc_profits.append(profit.mean())
    mcqstar = list(qs)[mc_profits.index(max(mc_profits))]

    
    # MC and newsvendor problem discussion
    st.markdown('## Monte Carlo Simulation')
    st.markdown(f"""
The Newsvendor Critical Ratio helps us determine the optimal order quantity:

$$CR = \\frac{{p - c}}{{p - s}} = \\frac{{{P} - {C}}}{{{P} - {S}}} = {c_ratio:.3f}$$

Using the inverse normal CDF:

$$Q^* = \\mu + z_{{CR}} \\cdot \\sigma = {mean} + {norm.ppf(c_ratio):.2f} \\times {std} \\approx {Qs}$$

Q* tells us the optimal number of newspapers to order each day in order to maximize profits. We can confirm this by completing Monte Carlo simulation. 
After running 1,000,000 simulated days, the order quantity that 
maximizes average profit converges to **Q* = {mcqstar} papers/day**.
""")

    fig3 = go.Figure()
    fig3.add_scatter(x=list(qs), y=mc_profits, mode="lines",name="Expected Profit")
    fig3.add_vline(x=mcqstar, line_dash="dash", annotation_text=f"Q*={mcqstar}", annotation_position="bottom right")
    fig3.update_layout(
        title="Monte Carlo Simulation: Expected Profit vs. Order Quantity (1,000,000 trials)",
        xaxis_title="Order Quantity", yaxis_title="Expected Daily Profit ($)")
    st.plotly_chart(fig3, use_container_width=True)


# ── GAME SCREEN ────────────────────────────────────────────────────────────────
else:
    day = st.session_state.day
    st.markdown(f'### Day {day} of {days}')
    # ── ORDER PHASE ────────────────────────────────────────────────────────────
    if st.session_state.phase == "order":
        st.markdown(f"### Choose how many papers you will order today")

        
        st.markdown(f'**Demand is normally distributed: Mean={mean}, Standard Deviation={std}**')
        order = st.slider("Order quantity", min_value=0, max_value=200,value=st.session_state.order_qty,step=1, key=f"slider_day_{day}")
        st.session_state.order_qty = order

        if st.button(f"Order {order} papers →"):
            demand = int(max(0, np.random.normal(mean, std)))
            st.session_state.demand_today = demand
            st.session_state.phase = "reveal"
            st.rerun()

    # ── REVEAL PHASE ──────────────────────────────────────────────────────────
    elif st.session_state.phase == "reveal":
        order  = st.session_state.order_qty
        demand = st.session_state.demand_today
        profit, sold, left, short = compute_profit(order, demand)

        st.markdown(f"### Results")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("You ordered", f"{order} papers")
        with col2:
            st.metric("Demand was", f"{demand} papers")
        with col3:
            leftover_str = f"{left} left" if left > 0 else f"{short} short"
            st.metric("Outcome", leftover_str)

        if profit >= 0:
            st.success(f'You made a profit of ${profit:,.2f}')
        else:
            st.error(f'You had a loss of ${profit:,.2f}')

        if left > 0:
            st.info(f"You had {left} unsold papers salvaged at 5 cents each (${left*S:.2f} recovered).")
        if short > 0:
            st.info(f"You ran out and missed {short} potential sales (lost revenue of ${short*(P-C):.2f}).")

        # Save to history
        if len(st.session_state.history) < day:
            st.session_state.history.append({
                "day": day, "order": order, "demand": demand,
                "profit": profit, "sold": sold,
                "leftover": left, "shortage": short
            })


        # Next button
        if day < days:
            if st.button(f" Go to day {day + 1}"):
                st.session_state.day  += 1
                st.session_state.phase = "order"
                st.rerun()
        else:
            if st.button("See Final Results!"):
                st.session_state.phase = "done"
                st.rerun()
