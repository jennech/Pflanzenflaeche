from __future__ import annotations

from typing import Mapping

from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView


class ResultsTable(QTableWidget):
    """Small helper table for displaying analysis results."""

    def __init__(self) -> None:
        super().__init__(4, 2)
        self.setHorizontalHeaderLabels(["Kennzahl", "Wert"])
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setSelectionMode(QTableWidget.NoSelection)
        self.setAlternatingRowColors(True)
        self.update_results(
            {
                "Gruene Pixel": "-",
                "Petrischalenflaeche": "-",
                "Pflanzenflaeche": "-",
                "Flaechenbedeckung": "-",
            }
        )

    def update_results(self, values: Mapping[str, str]) -> None:
        for row, (label, value) in enumerate(values.items()):
            self.setItem(row, 0, QTableWidgetItem(label))
            self.setItem(row, 1, QTableWidgetItem(value))
