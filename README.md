# HR Attrition Dashboard (Excel)

**Level: beginner to intermediate.** An Excel dashboard on employee attrition:
pivot tables, slicers and charts on a 1,470-employee dataset. The part I'm proud of is
what happened when I went back and checked it: I found that my first version
answered the wrong question, and the corrected version reaches different conclusions.

![Dashboard](images/Dashboard.png)

## The data

`data/hr_attrition.csv` is the public IBM HR Analytics "Employee Attrition &
Performance" sample dataset that people use to practise: 1,470 employees, 237 of whom
left. It's fictional data, not a real company's staff. I dropped the columns that
never change and the helper columns the workbook had added.

## What was wrong with my first dashboard

Three of the pivot tables (Job Role, Age-Group, Marital Status) used
**Count of CF_attrition count**. That counts every employee in the group, so it
measures how big the group is, not how many left. Each of those tables added up to
1,470 (everyone) instead of 237 (the leavers). A chart called "Attrition By
Age-Group" was really a chart of headcount by age.

Even where the counts were right, they were the wrong thing to look at. My README
said R&D was the high-turnover department because it had 56% of all leavers. R&D
is simply the biggest department. What matters is the **rate**, the share of a
group's people who left:

| Department | Employees | Leavers | Share of all leavers (what I reported) | **Attrition rate** |
|---|---:|---:|---:|---:|
| R&D | 961 | 133 | 56.1% | **13.8%** (lowest) |
| Sales | 446 | 92 | 38.8% | **20.6%** (highest) |
| HR | 63 | 12 | 5.1% | **19.0%** |

The same mistake hid the age pattern. "25-34" has the most leavers (112) because it's
the biggest age group, but the group that leaves most often is **under 25: 38 of 97,
39.2%**, about four times the rate of the 35-54 groups (about 10%).

## What I changed

- The three pivots now sum leavers (their totals are 237).
- A new sheet, **Attrition Rates**, gives employees, leavers, rate and share of
  leavers for six groupings, using live `COUNTIFS` formulas over the data table.
- Two dashboard charts ("Job Role" and "Marital-Status") had turned into "This
  chart isn't available in your version of Excel" placeholders. I replaced them with
  ordinary charts of the attrition rate.
- Titles now say what each chart shows ("Leavers By Education", "Share Of Leavers By
  Department", "Attrition Rate By Job Role").

## What goes with leaving

Company-wide, 16.1% left. I compared every group against that, showing how many
times higher or lower the group's rate is ("lift") and a 95% interval, because a group of 50 people can
look dramatic by chance. Groups under 50 are never ranked.

| Group | Employees | Leavers | Rate | Lift |
|---|---:|---:|---:|---:|
| Sales Representative | 83 | 33 | 39.8% | 2.5x |
| Under 25 | 97 | 38 | 39.2% | 2.4x |
| 0-1 years at the company | 215 | 75 | 34.9% | 2.2x |
| Works overtime | 416 | 127 | 30.5% | 1.9x |
| Lowest income quartile | 369 | 108 | 29.3% | 1.8x |
| Single | 470 | 120 | 25.5% | 1.6x |
| Does not work overtime | 1,054 | 110 | 10.4% | 0.6x |

To make it easy to follow I counted three flags per person: **works overtime,
single, under 30**.

| Flags | Employees | Leavers | Rate |
|---|---:|---:|---:|
| 0 | 574 | 41 | 7.1% |
| 1 | 620 | 81 | 13.1% |
| 2 | 236 | 88 | 37.3% |
| 3 | 40 | 27 | 67.5% |

Read this carefully: it describes who left in this dataset. It doesn't prove why
anyone left, and these factors overlap (junior people are younger, paid less and newer).
The three-flag group is only 40 people, so its 67.5% is a rough figure (the 95%
interval is wide). It's also a simple count, not a prediction model.

The full tables are in `output/attrition_rates.md` and `output/attrition_drivers.md`.

## Running it

```bash
pip install -r requirements.txt
python verify_numbers.py          # print every table above
python verify_numbers.py --save   # also write output/*.md
python -m pytest tests -q         # 11 tests
```

The tests work out expected values separately (a plain `csv` count of leavers, a
check that every group table adds up to 1,470 and 237, known values for the
interval formula) and compare them with the numbers stored inside the Excel
workbook, so the workbook and the Python can't disagree quietly.

## Files

```
HR-Employee-Analysis.xlsx   the dashboard (slicers, pivots, charts, Attrition Rates sheet)
data/hr_attrition.csv       the data
verify_numbers.py           every number in this README, recomputed
output/                     the tables it writes
tests/test_numbers.py       tests, including the Excel workbook's stored results
images/Dashboard.png        screenshot of the dashboard
```

Built with Excel (pivot tables, slicers, `COUNTIFS`) and Python (pandas, pytest).

## Limits

- It's a practice dataset, so treat the findings as a demonstration of the method
  and not as facts about any real company.
- The Age-Group chart still shows counts of leavers by age (now correctly labelled).
  For the age *rate* use the Attrition Rates sheet or the table above.

Muhammad Adnan, [LinkedIn](https://linkedin.com/in/muhammad-adnan-740336293),
adnandanish0404@gmail.com
