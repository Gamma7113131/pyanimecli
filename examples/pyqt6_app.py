
# Full-featured PyQt6 anime browser using pyanimecli
# Features: search, show info, recent/top airing, genres, episode list
# Each section is explained with comments.

import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QTextEdit, QListWidget, QListWidgetItem, QLabel, QComboBox
)
import pyanimecli as pac

class AnimeSearchApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Anime Browser (pyanimecli)")
        self.setGeometry(100, 100, 900, 600)

        # Main layout
        main_layout = QVBoxLayout()

        # --- Search bar ---
        search_layout = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search anime...")
        self.search_btn = QPushButton("Search")
        search_layout.addWidget(self.search_box)
        search_layout.addWidget(self.search_btn)
        main_layout.addLayout(search_layout)

        # --- Quick actions ---
        quick_layout = QHBoxLayout()
        self.recent_btn = QPushButton("Recent Episodes")
        self.top_btn = QPushButton("Top Airing")
        self.genres_combo = QComboBox()
        self.genres_combo.addItem("Select Genre...")
        # Populate genres from API
        try:
            genres = pac.genres()
            for g in genres:
                self.genres_combo.addItem(g)
        except Exception:
            pass
        quick_layout.addWidget(self.recent_btn)
        quick_layout.addWidget(self.top_btn)
        quick_layout.addWidget(self.genres_combo)
        main_layout.addLayout(quick_layout)

        # --- Results list ---
        self.results_list = QListWidget()
        main_layout.addWidget(QLabel("Results:"))
        main_layout.addWidget(self.results_list)

        # --- Info/Details area ---
        self.info_area = QTextEdit()
        self.info_area.setReadOnly(True)
        main_layout.addWidget(QLabel("Details:"))
        main_layout.addWidget(self.info_area)

        self.setLayout(main_layout)

        # --- Connect signals ---
        self.search_btn.clicked.connect(self.do_search)
        self.recent_btn.clicked.connect(self.show_recent)
        self.top_btn.clicked.connect(self.show_top)
        self.genres_combo.currentIndexChanged.connect(self.genre_selected)
        self.results_list.itemClicked.connect(self.show_info)

        # --- Initial state ---
        self.current_results = []  # Store current search results

    def do_search(self):
        """Search for anime by name."""
        query = self.search_box.text().strip()
        if not query:
            self.info_area.setText("Enter a search term.")
            return
        self.info_area.setText(f"Searching for '{query}'...")
        try:
            results = pac.search(query)
            self.populate_results(results)
        except Exception as e:
            self.info_area.setText(f"Error: {e}")

    def show_recent(self):
        """Show recent episodes."""
        self.info_area.setText("Loading recent episodes...")
        try:
            results = pac.recent_episodes()
            self.populate_results(results)
        except Exception as e:
            self.info_area.setText(f"Error: {e}")

    def show_top(self):
        """Show top airing anime."""
        self.info_area.setText("Loading top airing anime...")
        try:
            results = pac.top_airing()
            self.populate_results(results)
        except Exception as e:
            self.info_area.setText(f"Error: {e}")

    def genre_selected(self, idx):
        """Search by selected genre."""
        genre = self.genres_combo.currentText()
        if idx == 0 or not genre or genre == "Select Genre...":
            return
        self.info_area.setText(f"Searching for genre: {genre}")
        try:
            results = pac.genre_search(genre)
            self.populate_results(results)
        except Exception as e:
            self.info_area.setText(f"Error: {e}")

    def populate_results(self, results):
        """Populate the results list with anime titles."""
        self.results_list.clear()
        self.current_results = results
        if not results:
            self.results_list.addItem("No results found.")
            self.info_area.setText("")
            return
        for anime in results:
            title = anime.get("title", "Unknown")
            aid = anime.get("id", "")
            item = QListWidgetItem(f"{title} ({aid})")
            self.results_list.addItem(item)
        self.info_area.setText("Select an anime to view details.")

    def show_info(self, item):
        """Show detailed info for selected anime."""
        idx = self.results_list.row(item)
        if idx < 0 or idx >= len(self.current_results):
            self.info_area.setText("No details available.")
            return
        anime = self.current_results[idx]
        aid = anime.get("id", "")
        try:
            info = pac.info(aid)
            # Format info nicely
            text = f"Title: {info.get('title', 'N/A')}\n"
            text += f"Type: {info.get('type', 'N/A')}\n"
            text += f"Status: {info.get('status', 'N/A')}\n"
            text += f"Genres: {', '.join(info.get('genres', []))}\n"
            text += f"Total Episodes: {info.get('total_episodes', 'N/A')}\n"
            text += f"Description:\n{info.get('description', 'N/A')}\n\n"
            # Show episode list if available
            episodes = info.get('episodes', [])
            if episodes:
                text += "Episodes:\n"
                for ep in episodes:
                    text += f"  Ep {ep.get('number', '?')}: {ep.get('title', '')} (ID: {ep.get('id', '')})\n"
            self.info_area.setText(text)
        except Exception as e:
            self.info_area.setText(f"Error loading info: {e}")

# --- Run the app ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = AnimeSearchApp()
    win.show()
    sys.exit(app.exec())