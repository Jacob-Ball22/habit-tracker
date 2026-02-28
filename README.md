# Habit Tracker

A desktop habit tracking app built with Python and PyQt6. Organise habits into Focus Areas, mark daily completions, and visualise your consistency with a GitHub-style contribution heatmap.

![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![PyQt6](https://img.shields.io/badge/PyQt6-6.6%2B-green)
![SQLite](https://img.shields.io/badge/Storage-SQLite-lightgrey)

## Features

- **Focus Areas** — Group habits into categories (Health, Fitness, Learning, etc.) and filter the main view by area
- **Habit cards** — Each habit shows a name, optional description, completion button, total count, and heatmap
- **GitHub-style heatmap** — 52-week × 7-day grid showing your completion history at a glance
- **Add / Edit / Delete** habits and Focus Areas at any time
- **Light & Dark mode** — Switch themes from the ⚙ settings button in the top right
- **Fully local** — All data stored in a local SQLite database; no accounts or internet required

## Setup

**Requirements:** Python 3.11+

```bash
pip install -r requirements.txt
python main.py
```

## Project Structure

```
habit-tracker/
├── main.py                     # Entry point
├── requirements.txt
├── data/
│   └── habits.db               # SQLite database (auto-created on first run)
└── src/
    ├── db.py                   # Database layer (CRUD)
    ├── models.py               # Dataclass models
    ├── utils.py                # Date helpers
    └── ui/
        ├── main_window.py      # App window, stylesheets, theme switching
        ├── sidebar.py          # Focus Area filter sidebar
        ├── habit_view.py       # Habit card list
        ├── heatmap_widget.py   # Contribution heatmap component
        ├── dialogs.py          # Add/Edit dialogs
        └── settings_dialog.py  # Light/Dark mode settings
```

## Usage

1. **Add a Focus Area** — Click the `+` next to "Focus Areas" in the sidebar
2. **Add a Habit** — Click the `+` next to "Add Habit" in the sidebar
3. **Mark complete** — Click "Mark Complete Today" on any habit card; click again to undo
4. **Filter by Focus Area** — Click any area in the sidebar to filter the habit list
5. **Change theme** — Click ⚙ in the top right and choose Default (Light) or Dark Mode

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| UI | PyQt6 |
| Storage | SQLite (built-in `sqlite3`) |
| Heatmap | Custom QPainter rendering |

## Future Improvements
- Add capabilities to attach daily/weekly habits to your calendar of choice or a push notification to your mobile device
- Add ability to seperate chart by months
- Be able to change tracking chart to track progress by each week or each month

## Author
Jacob Ball — Master's in Data Science, Fordham University