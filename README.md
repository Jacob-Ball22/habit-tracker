# FluxFolio (Habit Tracker)

A desktop habit tracking app built with Python and PyQt6. Organise habits into Focus Areas, mark daily completions, and visualise your consistency with a GitHub-style contribution heatmap.

![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![PyQt6](https://img.shields.io/badge/PyQt6-6.6%2B-green)
![SQLite](https://img.shields.io/badge/Storage-SQLite-lightgrey)

## Features

- **Focus Areas** — Group habits into categories (Health, Fitness, Learning, etc.) and filter the main view by area
- **Habit cards** — Each habit shows a name, optional description, completion button, streak, and weekly/monthly completion rates
- **GitHub-style heatmap** — 52-week × 7-day grid showing your completion history at a glance
- **Bar chart view** — Toggle each card between heatmap and a 52-week bar chart showing weekly completion counts
- **Streak & completion stats** — Current streak, week rate (Mon–today), and month rate displayed on every card
- **Frequency scheduling** — Set which days of the week a habit is active; unscheduled habits are shown separately
- **Drag-and-drop reorder** — Drag the handle on any card to rearrange habits; order persists across restarts
- **Archive & restore** — Archive habits to hide them without losing history; restore them any time from the sidebar
- **Add / Edit / Delete** habits and Focus Areas at any time
- **Export to CSV** — Export all habit data from Settings for use in spreadsheets or analysis tools
- **Light & Dark mode** — Switch themes from the ⚙ settings button in the top right
- **Fully local** — All data stored in a local SQLite database; no accounts or internet required

## Getting Started

### Prerequisites

- Python 3.11 or higher — [Download Python](https://www.python.org/downloads/)
- Git — [Download Git](https://git-scm.com/downloads)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/habit-tracker.git
   cd habit-tracker
   ```

2. **Create and activate a virtual environment** (recommended)
   ```bash
   # macOS / Linux
   python3 -m venv venv
   source venv/bin/activate

   # Windows
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the app**
   ```bash
   python main.py
   ```

The SQLite database is created automatically at `data/habits.db` on first launch — no additional setup required.

## Project Structure

```
habit-tracker/
├── main.py                     # Entry point
├── requirements.txt
├── data/
│   └── habits.db               # SQLite database (auto-created on first run)
└── src/
    ├── db.py                   # Database layer (CRUD, archive, reorder, CSV export)
    ├── models.py               # Dataclass models
    ├── utils.py                # Date helpers
    └── ui/
        ├── main_window.py      # App window, stylesheets, theme switching
        ├── sidebar.py          # Focus Area filter + Archived section
        ├── habit_view.py       # Habit card list with drag-and-drop reorder
        ├── heatmap_widget.py   # Contribution heatmap component
        ├── bar_chart_widget.py # 52-week bar chart component
        ├── dialogs.py          # Add/Edit dialogs with frequency scheduling
        └── settings_dialog.py  # Theme + CSV export settings
```

## Usage

1. **Add a Focus Area** — Click the `+` next to "Focus Areas" in the sidebar
2. **Add a Habit** — Click the `+` next to "Add Habit" in the sidebar; set the name, Focus Area, and which days of the week it applies
3. **Mark complete** — Click "Mark Complete Today" on any habit card; click again to undo
4. **Reorder habits** — Drag the `⠿` handle on any card to rearrange the order
5. **Switch chart view** — Click the `📊` button on a card to toggle between heatmap and bar chart
6. **Archive a habit** — Click "Archive" on a card to hide it without losing history
7. **View / restore archived** — Click "Archived" at the bottom of the sidebar; click "Restore" on any card to bring it back
8. **Filter by Focus Area** — Click any area in the sidebar to filter the habit list
9. **Export data** — Click ⚙ → "Export Data to CSV…" to save all habit history as a CSV file
10. **Change theme** — Click ⚙ in the top right and choose Default (Light) or Dark Mode

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| UI | PyQt6 |
| Storage | SQLite (built-in `sqlite3`) |
| Heatmap & Charts | Custom QPainter rendering |

## Future Improvements
- Add capabilities to attach daily/weekly habits to your calendar of choice or a push notification to your mobile device
- Add ability to seperate chart by months
- Be able to change tracking chart to track progress by each week or each month

## Author
Jacob Ball — Master's in Data Science, Fordham University
