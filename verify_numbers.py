"""Recompute every number quoted in the README from data/hr_attrition.csv.

    python verify_numbers.py          # print the tables
    python verify_numbers.py --save   # also write output/*.md

Three things happen here:

1. Attrition RATE by group. The first version of the dashboard counted people
   ("Count of CF_attrition count") in three pivots, so those charts showed how
   many employees a group had, not how many left. Rates fix that.
2. Driver ranking. Every value of every factor is compared with the company-wide
   rate (16.1%). "Lift" is how many times higher (or lower) the group's rate is,
   and a 95% Wilson interval shows how much to trust it, because a group of 50
   people can look dramatic by chance.
3. A three-flag risk profile: overtime, single, under 30. It is deliberately just
   counting flags, so anyone can follow it. It describes who left in this data;
   it is not a prediction model and it doesn't prove why anyone left.
"""

import math
import os
import sys

import pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(ROOT, "data", "hr_attrition.csv")
MIN_GROUP = 50  # smaller groups are shown but never ranked

AGE_BANDS = ["Under 25", "25 - 34", "35 - 44", "45 - 54", "Over 55"]


def load():
    df = pd.read_csv(CSV)
    df["left"] = (df["Attrition"] == "Yes").astype(int)
    df["Age band"] = pd.cut(df["Age"], [0, 24, 34, 44, 54, 200], labels=AGE_BANDS).astype(str)
    df["Income quartile"] = pd.qcut(
        df["Monthly Income"], 4, labels=["Q1 (lowest)", "Q2", "Q3", "Q4 (highest)"]).astype(str)
    df["Tenure"] = pd.cut(df["Years At Company"], [-1, 1, 3, 5, 10, 100],
                          labels=["0-1 yrs", "2-3 yrs", "4-5 yrs", "6-10 yrs", "11+ yrs"]).astype(str)
    df["Years since promotion"] = pd.cut(df["Years Since Last Promotion"], [-1, 0, 2, 5, 100],
                                         labels=["this year", "1-2 yrs", "3-5 yrs", "6+ yrs"]).astype(str)
    df["Distance from home"] = pd.cut(df["Distance From Home"], [0, 5, 10, 20, 100],
                                      labels=["1-5", "6-10", "11-20", "21+"]).astype(str)
    df["risk_flags"] = ((df["Over Time"] == "Yes").astype(int)
                        + (df["Marital Status"] == "Single").astype(int)
                        + (df["Age"] < 30).astype(int))
    return df


def wilson(leavers, n, z=1.96):
    """95% Wilson score interval for a proportion."""
    if n == 0:
        return (0.0, 0.0)
    p = leavers / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (centre - half, centre + half)


def rate_table(df, column):
    g = df.groupby(column).agg(employees=("left", "size"), leavers=("left", "sum"))
    g["rate"] = g["leavers"] / g["employees"]
    g["share_of_leavers"] = g["leavers"] / g["leavers"].sum()
    return g.sort_values("rate", ascending=False)


def drivers(df, features):
    base = df["left"].mean()
    rows = []
    for f in features:
        for value, grp in df.groupby(f):
            n, leavers = len(grp), int(grp["left"].sum())
            lo, hi = wilson(leavers, n)
            rows.append({"factor": f, "value": str(value), "employees": n, "leavers": leavers,
                         "rate": leavers / n, "lift": (leavers / n) / base, "ci_low": lo, "ci_high": hi})
    out = pd.DataFrame(rows)
    return out[out["employees"] >= MIN_GROUP].sort_values("lift", ascending=False)


def risk_profile(df):
    g = df.groupby("risk_flags").agg(employees=("left", "size"), leavers=("left", "sum"))
    g["rate"] = g["leavers"] / g["employees"]
    return g


def pct(x, d=1):
    return f"{100 * x:.{d}f}%"


def md_table(frame, columns, formats):
    head = "| " + " | ".join(columns) + " |\n|" + "|".join("---" for _ in columns) + "|\n"
    body = ""
    for _, row in frame.iterrows():
        body += "| " + " | ".join(formats[c](row[c]) if c in formats else str(row[c]) for c in columns) + " |\n"
    return head + body


FEATURES = ["Over Time", "Marital Status", "Age band", "Job Role", "Department", "Business Travel",
            "Education Field", "Gender", "Income quartile", "Tenure", "Years since promotion",
            "Distance from home", "Job Level", "Stock Option Level", "Job Satisfaction",
            "Work Life Balance", "Environment Satisfaction", "Job Involvement"]


def main(argv):
    df = load()
    base = df["left"].mean()
    print(f"employees: {len(df):,}  leavers: {int(df['left'].sum())}  attrition rate: {pct(base, 2)}")

    sections = {"rates": ["# Attrition rate by group", "",
                          f"Company-wide: {int(df['left'].sum())} of {len(df):,} left ({pct(base, 2)}).", ""]}
    for column in ["Department", "Age band", "Marital Status", "Job Role", "Education", "Over Time"]:
        t = rate_table(df, column).reset_index()
        print(f"\n{column}\n{t.to_string(index=False, formatters={'rate': pct, 'share_of_leavers': pct})}")
        sections["rates"] += [f"## {column}", "", md_table(
            t, [column, "employees", "leavers", "rate", "share_of_leavers"],
            {"rate": pct, "share_of_leavers": pct})]

    d = drivers(df, FEATURES)
    print(f"\nTop drivers (groups of {MIN_GROUP}+ people):")
    print(d.head(12).to_string(index=False, float_format=lambda x: f"{x:.3f}"))
    rp = risk_profile(df).reset_index()
    print("\nRisk flags (overtime, single, under 30):")
    print(rp.to_string(index=False, formatters={"rate": pct}))

    fmt = {"rate": pct, "lift": lambda x: f"{x:.2f}x",
           "ci": lambda x: x}
    d = d.assign(ci=[f"{pct(a, 0)} to {pct(b, 0)}" for a, b in zip(d["ci_low"], d["ci_high"])])
    sections["drivers"] = [
        "# What goes with leaving", "",
        f"Company-wide attrition is {pct(base)}. **Lift** is a group's rate divided by that. "
        f"The interval is a 95% Wilson interval: the wider it is, the less you should read into "
        f"the rate. Only groups of {MIN_GROUP}+ people are ranked.", "",
        "This describes who left in this dataset. It doesn't show *why* people left, and "
        "several of these factors overlap (junior people are also younger, lower paid and newer).", "",
        "## Highest and lowest", "",
        md_table(pd.concat([d.head(12), d.tail(6)]),
                 ["factor", "value", "employees", "leavers", "rate", "lift", "ci"], fmt), "",
        "## Three flags: overtime, single, under 30", "",
        md_table(rp, ["risk_flags", "employees", "leavers", "rate"], {"rate": pct}), ""]

    if "--save" in argv:
        os.makedirs(os.path.join(ROOT, "output"), exist_ok=True)
        for name, file in (("rates", "attrition_rates.md"), ("drivers", "attrition_drivers.md")):
            with open(os.path.join(ROOT, "output", file), "w", encoding="utf-8", newline="\n") as f:
                f.write("\n".join(sections[name]))
        print("\nsaved output/attrition_rates.md and output/attrition_drivers.md")


if __name__ == "__main__":
    main(sys.argv[1:])
