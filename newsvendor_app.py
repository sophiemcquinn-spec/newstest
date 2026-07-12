import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from scipy.stats import norm

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="The Newsvendor Game",
    page_icon="📰",
    layout="centered",
)

# ── Constants ──────────────────────────────────────────────────────────────────
PRICE      = 1.50   # selling price per paper
COST       = 0.75   # purchase cost per paper
SALVAGE    = 0.10   # salvage value per unsold paper
MU         = 100    # mean daily demand
SIGMA      = 25     # std dev of daily demand
DAYS       = 7
OVERAGE    = COST - SALVAGE          # cost of ordering too much
UNDERAGE   = PRICE - COST            # cost of ordering too little
CR         = UNDERAGE / (UNDERAGE + OVERAGE)   # critical ratio
Q_STAR     = int(norm.ppf(CR, MU, SIGMA))      # optimal order quantity

# ── Session state init ─────────────────────────────────────────────────────────
def init_state():
    if "day" not in st.session_state:
        st.session_state.day        = 1
        st.session_state.history    = []   # list of dicts per day
        st.session_state.phase      = "order"   # "order" | "reveal" | "done"
        st.session_state.order_qty  = Q_STAR
        st.session_state.demand_today = None
        np.random.seed()   # fresh seed each game

init_state()

# ── Helpers ────────────────────────────────────────────────────────────────────
def compute_profit(order, demand):
    sold     = min(order, demand)
    leftover = max(0, order - demand)
    shortage = max(0, demand - order)
    revenue  = sold * PRICE
    salvage  = leftover * SALVAGE
    cost     = order * COST
    profit   = revenue + salvage - cost
    return profit, sold, leftover, shortage

def running_total():
    return sum(r["profit"] for r in st.session_state.history)

def profit_color(val):
    return "green" if val >= 0 else "red"

def reset_game():
    for key in ["day","history","phase","order_qty","demand_today"]:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

# ── Styling ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  .big-metric   { font-size:2.4rem; font-weight:700; }
  .label        { font-size:0.8rem; color:#888; text-transform:uppercase; letter-spacing:.05em; }
  .day-badge    { background:#1f77b4; color:white; border-radius:20px;
                  padding:4px 16px; font-weight:600; display:inline-block; }
  .profit-pos   { color:#2ca02c; font-weight:700; }
  .profit-neg   { color:#d62728; font-weight:700; }
  .info-box     { background:#f0f4ff; border-left:4px solid #1f77b4;
                  padding:12px 16px; border-radius:4px; margin:8px 0; }
  .result-box   { background:#f9f9f9; border-radius:8px; padding:16px; margin:12px 0; }
  .stButton>button { width:100%; font-size:1.05rem; font-weight:600; padding:10px; }
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("# 📰 The Newsvendor Game")
st.markdown("*Run your newsstand for a week. Order smart — demand is uncertain!*")

# ── Economics sidebar ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📋 Economics")
    st.markdown(f"""
| Item | Value |
|------|-------|
| Selling price | **${PRICE:.2f}** / paper |
| Purchase cost | **${COST:.2f}** / paper |
| Salvage value | **${SALVAGE:.2f}** / paper |
| Avg demand (μ) | **{MU}** papers/day |
| Std deviation (σ) | **{SIGMA}** papers/day |
""")
    st.divider()
    st.markdown("### 💡 How it works")
    st.markdown("""
- Each morning you order papers
- Demand is drawn from a **Normal distribution**
- Unsold papers are salvaged at a loss
- Unmet demand = lost revenue
- Maximize your **7-day total profit!**
""")
    st.divider()
    if st.session_state.phase != "done":
        total = running_total()
        color = "profit-pos" if total >= 0 else "profit-neg"
        st.markdown(f"### Running Total")
        st.markdown(f'<p class="{color}" style="font-size:1.8rem">${total:,.2f}</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="label">after {len(st.session_state.history)} day(s)</p>', unsafe_allow_html=True)

    st.divider()
    if st.button("🔄 Restart Game"):
        reset_game()

# ── DONE SCREEN ────────────────────────────────────────────────────────────────
if st.session_state.phase == "done":
    st.balloons()
    total   = running_total()
    hist_df = pd.DataFrame(st.session_state.history)

    # Theoretical optimal for comparison
    opt_profits = []
    for row in st.session_state.history:
        p, *_ = compute_profit(Q_STAR, row["demand"])
        opt_profits.append(p)
    opt_total = sum(opt_profits)

    st.markdown("---")
    st.markdown("## 🏁 Week Complete!")

    col1, col2, col3 = st.columns(3)
    with col1:
        color = "profit-pos" if total >= 0 else "profit-neg"
        st.markdown('<p class="label">Your Total Profit</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="{color}" style="font-size:2rem;font-weight:700">${total:,.2f}</p>', unsafe_allow_html=True)
    with col2:
        st.markdown('<p class="label">Optimal Q* Total</p>', unsafe_allow_html=True)
        st.markdown(f'<p style="font-size:2rem;font-weight:700;color:#1f77b4">${opt_total:,.2f}</p>', unsafe_allow_html=True)
    with col3:
        gap = total - opt_total
        g_color = "profit-pos" if gap >= 0 else "profit-neg"
        st.markdown('<p class="label">vs. Optimal</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="{g_color}" style="font-size:2rem;font-weight:700">{("+" if gap>=0 else "")}{gap:,.2f}</p>', unsafe_allow_html=True)

    # Grade
    pct = (total / opt_total * 100) if opt_total != 0 else 0
    if   pct >= 95: grade, msg = "A+", "🏆 Near-perfect! You intuitively found the optimum."
    elif pct >= 85: grade, msg = "A",  "🌟 Excellent week — very close to optimal ordering."
    elif pct >= 75: grade, msg = "B",  "👍 Good job! A bit of fine-tuning would help."
    elif pct >= 60: grade, msg = "C",  "📚 Decent, but there's room to improve your ordering strategy."
    else:           grade, msg = "D",  "📉 Tough week! Try ordering closer to average demand."

    st.markdown(f'<div class="info-box"><b>Grade: {grade}</b> &nbsp;|&nbsp; {msg}</div>', unsafe_allow_html=True)

    # Daily profit chart
    fig = go.Figure()
    fig.add_bar(
        x=[f"Day {r['day']}" for r in st.session_state.history],
        y=[r["profit"] for r in st.session_state.history],
        marker_color=["#2ca02c" if r["profit"] >= 0 else "#d62728" for r in st.session_state.history],
        name="Your Profit"
    )
    fig.add_scatter(
        x=[f"Day {r['day']}" for r in st.session_state.history],
        y=opt_profits,
        mode="lines+markers", name=f"Optimal Q*={Q_STAR}",
        line=dict(color="#1f77b4", dash="dash"), marker=dict(size=7)
    )
    fig.update_layout(
        title="Daily Profit: Your Orders vs. Optimal Q*",
        yaxis_title="Profit ($)", xaxis_title="",
        legend=dict(orientation="h", y=1.12),
        plot_bgcolor="white", height=340
    )
    fig.update_yaxes(gridcolor="#eee", zeroline=True, zerolinecolor="#ccc")
    st.plotly_chart(fig, use_container_width=True)

    # Demand vs order scatter
    fig2 = go.Figure()
    fig2.add_scatter(
        x=[f"Day {r['day']}" for r in st.session_state.history],
        y=[r["demand"] for r in st.session_state.history],
        mode="lines+markers", name="Actual Demand",
        line=dict(color="#ff7f0e"), marker=dict(size=8)
    )
    fig2.add_scatter(
        x=[f"Day {r['day']}" for r in st.session_state.history],
        y=[r["order"] for r in st.session_state.history],
        mode="lines+markers", name="Your Order",
        line=dict(color="#9467bd"), marker=dict(size=8, symbol="square")
    )
    fig2.add_hline(y=Q_STAR, line_dash="dot", line_color="#1f77b4",
                   annotation_text=f"Q*={Q_STAR}", annotation_position="right")
    fig2.update_layout(
        title="Your Orders vs. Realized Demand",
        yaxis_title="Papers", xaxis_title="",
        legend=dict(orientation="h", y=1.12),
        plot_bgcolor="white", height=300
    )
    fig2.update_yaxes(gridcolor="#eee")
    st.plotly_chart(fig2, use_container_width=True)

    # Summary table
    st.markdown("### 📊 Day-by-Day Breakdown")
    display_df = pd.DataFrame([{
        "Day": r["day"],
        "Ordered": r["order"],
        "Demand": r["demand"],
        "Sold": r["sold"],
        "Leftover": r["leftover"],
        "Shortage": r["shortage"],
        "Profit": f"${r['profit']:.2f}"
    } for r in st.session_state.history])
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    
        # Monte Carlo simulation test
        qs = range(0,200,1)
        mc_profits = []
        for q in qs:
            demand = np.random.normal(MU,SIGMA,10000).clip(0)
            profit = np.minimum(demand,q)*PRICE + np.maximum(0,q-demand)*SALVAGE-q*COST
            mc_profits.append(profit.mean())
        mcqstar = list(qs)[mc_profits.index(max(mc_profits))]    
    
    # Theory reveal
    with st.expander("📐 The Math Behind the Optimal Order Quantity"):
        st.markdown(f"""


The **Newsvendor Critical Ratio** gives the theoretically optimal order quantity:

$$CR = \\frac{{p - c}}{{p - s}} = \\frac{{{PRICE} - {COST}}}{{{PRICE} - {SALVAGE}}} = {CR:.3f}$$

This means you should order enough to satisfy demand **{CR*100:.1f}%** of the time.

Using the inverse normal CDF:

$$Q^* = \\mu + z_{{CR}} \\cdot \\sigma = {MU} + {norm.ppf(CR):.2f} \\times {SIGMA} \\approx {Q_STAR}$$

**Monte Carlo confirms this:** running 10,000 simulated weeks, the order quantity that 
maximizes average profit converges to **Q* = {mcqstar} papers/day**.
""")



        fig3 = go.Figure()
        fig3.add_scatter(x=list(qs), y=mc_profits, mode="lines",name="Expected Profit")
        fig3.add_vline(x=Q_STAR, line_dash="dash", line_color="#2ca02c",
                       annotation_text=f"Q*={Q_STAR}", annotation_position="top right")
        fig3.update_layout(
            title="Monte Carlo: Expected Profit vs. Order Quantity (10,000 trials)",
            xaxis_title="Order Quantity", yaxis_title="Expected Daily Profit ($)",
            plot_bgcolor="white", height=300
        )
        fig3.update_yaxes(gridcolor="#eee")
        st.plotly_chart(fig3, use_container_width=True)

    if st.button("🔄 Play Again"):
        reset_game()

# ── GAME SCREEN ────────────────────────────────────────────────────────────────
else:
    day = st.session_state.day
    st.markdown(f'<span class="day-badge">📅 Day {day} of {DAYS}</span>', unsafe_allow_html=True)

    # Progress bar
    st.progress((day - 1) / DAYS)
    st.markdown("")

    # ── ORDER PHASE ────────────────────────────────────────────────────────────
    if st.session_state.phase == "order":
        st.markdown(f"### ☀️ Good morning! How many papers will you order today?")

        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f'<p class="label">Demand is normally distributed: μ={MU}, σ={SIGMA}</p>', unsafe_allow_html=True)
            order = st.slider(
                "Order quantity (papers)",
                min_value=10, max_value=200,
                value=st.session_state.order_qty,
                step=1, key=f"slider_day_{day}"
            )
            st.session_state.order_qty = order

        with col2:
            st.markdown('<p class="label">Expected outcome</p>', unsafe_allow_html=True)
            # Quick expected profit preview
            demands_preview = np.random.normal(MU, SIGMA, 2000).clip(0)
            profits_preview = (np.minimum(demands_preview, order)*PRICE
                               + np.maximum(0, order-demands_preview)*SALVAGE
                               - order*COST)
            exp_profit = profits_preview.mean()
            color = "profit-pos" if exp_profit >= 0 else "profit-neg"
            st.markdown(f'<p class="{color}" style="font-size:1.4rem;font-weight:600">${exp_profit:.2f}</p>', unsafe_allow_html=True)
            st.markdown('<p class="label">avg profit at this qty</p>', unsafe_allow_html=True)

        # Demand distribution preview
        x = np.linspace(MU - 4*SIGMA, MU + 4*SIGMA, 300)
        y = norm.pdf(x, MU, SIGMA)
        fig = go.Figure()
        fig.add_scatter(x=x, y=y, mode="lines", fill="tozeroy",
                        fillcolor="rgba(31,119,180,0.15)", line=dict(color="#1f77b4"),
                        name="Demand distribution")
        fig.add_vline(x=order, line_color="#9467bd", line_width=2.5,
                      annotation_text=f"Your order: {order}", annotation_position="top right",
                      annotation_font_color="#9467bd")
        fig.add_vline(x=MU, line_dash="dot", line_color="#888", line_width=1,
                      annotation_text=f"μ={MU}", annotation_position="top left")
        fig.update_layout(
            height=200, margin=dict(l=10,r=10,t=30,b=10),
            xaxis_title="Demand (papers)", yaxis_title="",
            plot_bgcolor="white", showlegend=False
        )
        fig.update_yaxes(showticklabels=False, gridcolor="#eee")
        fig.update_xaxes(gridcolor="#eee")
        st.plotly_chart(fig, use_container_width=True)

        if st.button(f"📦 Lock in order of {order} papers →"):
            demand = int(max(0, np.random.normal(MU, SIGMA)))
            st.session_state.demand_today = demand
            st.session_state.phase = "reveal"
            st.rerun()

    # ── REVEAL PHASE ──────────────────────────────────────────────────────────
    elif st.session_state.phase == "reveal":
        order  = st.session_state.order_qty
        demand = st.session_state.demand_today
        profit, sold, leftover, shortage = compute_profit(order, demand)

        st.markdown(f"### 🌆 End of Day {day} — Results")
        st.markdown('<div class="result-box">', unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("You ordered", f"{order} papers")
        with col2:
            st.metric("Demand was", f"{demand} papers",
                      delta=f"{demand-order:+d} vs order")
        with col3:
            st.metric("Papers sold", f"{sold}")
        with col4:
            leftover_str = f"{leftover} left" if leftover > 0 else f"{shortage} short"
            st.metric("Outcome", leftover_str)

        st.markdown('</div>', unsafe_allow_html=True)

        color = "profit-pos" if profit >= 0 else "profit-neg"
        verdict = "🎉 Profitable day!" if profit >= 0 else "📉 Loss day."
        st.markdown(f"""
<div class="info-box">
  {verdict} &nbsp;
  <span class="{color}" style="font-size:1.4rem">${profit:,.2f}</span>
  &nbsp;today
</div>
""", unsafe_allow_html=True)

        if leftover > 0:
            st.info(f"You had **{leftover} unsold papers** salvaged at ${SALVAGE:.2f} each (${leftover*SALVAGE:.2f} recovered).")
        if shortage > 0:
            st.warning(f"You **ran out** and missed **{shortage} sales** — lost revenue of ${shortage*(PRICE-COST):.2f}.")

        # Save to history
        if len(st.session_state.history) < day:
            st.session_state.history.append({
                "day": day, "order": order, "demand": demand,
                "profit": profit, "sold": sold,
                "leftover": leftover, "shortage": shortage
            })

        # Running profit mini-chart
        if len(st.session_state.history) > 1:
            days_so_far = [f"Day {r['day']}" for r in st.session_state.history]
            cumulative  = np.cumsum([r["profit"] for r in st.session_state.history]).tolist()
            fig = go.Figure()
            fig.add_scatter(x=days_so_far, y=cumulative, mode="lines+markers",
                            line=dict(color="#1f77b4", width=2.5),
                            marker=dict(size=8), fill="tozeroy",
                            fillcolor="rgba(31,119,180,0.1)")
            fig.add_hline(y=0, line_color="#ccc", line_dash="dot")
            fig.update_layout(
                title="Cumulative Profit So Far",
                height=180, margin=dict(l=10,r=10,t=40,b=10),
                plot_bgcolor="white", showlegend=False,
                yaxis_title="$", yaxis_tickprefix="$"
            )
            fig.update_yaxes(gridcolor="#eee")
            st.plotly_chart(fig, use_container_width=True)

        # Next button
        if day < DAYS:
            if st.button(f"➡️ Proceed to Day {day + 1}"):
                st.session_state.day  += 1
                st.session_state.phase = "order"
                st.rerun()
        else:
            if st.button("🏁 See Final Results!"):
                st.session_state.phase = "done"
                st.rerun()
