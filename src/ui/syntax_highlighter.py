"""
Markdown Syntax Highlighter for PyQt6 QTextEdit
Provides real-time luxury highlighting for markdown specifications in Onyx and Vellum palettes.
"""

import re
from PyQt6.QtCore import QRegularExpression
from PyQt6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat


class MarkdownHighlighter(QSyntaxHighlighter):
    """Luxury Markdown syntax highlighter with Onyx and Vellum palette support."""

    def __init__(self, parent=None, theme: str = "onyx"):
        super().__init__(parent)
        self.theme = theme
        self.highlighting_rules = []
        self._init_formats()
        self._build_rules()

    def set_theme(self, theme: str):
        """Update theme ('onyx' or 'vellum') and re-highlight."""
        self.theme = theme.lower()
        self._init_formats()
        self._build_rules()
        self.rehighlight()

    def _init_formats(self):
        is_vellum = (self.theme == "vellum")

        # Heading 1 format
        self.h1_format = QTextCharFormat()
        self.h1_format.setFontWeight(QFont.Weight.Bold)
        self.h1_format.setForeground(QColor(184, 134, 11) if is_vellum else QColor(212, 175, 55))

        # Heading 2 & 3 format
        self.h2_format = QTextCharFormat()
        self.h2_format.setFontWeight(QFont.Weight.Bold)
        self.h2_format.setForeground(QColor(217, 119, 6) if is_vellum else QColor(245, 158, 11))

        # Bold format
        self.bold_format = QTextCharFormat()
        self.bold_format.setFontWeight(QFont.Weight.Bold)
        self.bold_format.setForeground(QColor(15, 23, 42) if is_vellum else QColor(243, 244, 246))

        # Italic format
        self.italic_format = QTextCharFormat()
        self.italic_format.setFontItalic(True)
        self.italic_format.setForeground(QColor(100, 116, 139) if is_vellum else QColor(156, 163, 175))

        # Code block / inline code format
        self.code_format = QTextCharFormat()
        self.code_format.setFontFamily("Consolas")
        self.code_format.setForeground(QColor(13, 148, 136) if is_vellum else QColor(56, 189, 248))

        # Bullet / checkbox format
        self.bullet_format = QTextCharFormat()
        self.bullet_format.setFontWeight(QFont.Weight.Bold)
        self.bullet_format.setForeground(QColor(194, 65, 12) if is_vellum else QColor(251, 191, 36))

        # Table & pipe format
        self.table_format = QTextCharFormat()
        self.table_format.setForeground(QColor(100, 116, 139) if is_vellum else QColor(107, 114, 128))

    def _build_rules(self):
        self.highlighting_rules.clear()

        # Heading 1: # Title
        self.highlighting_rules.append((
            QRegularExpression(r"^#[^#\n].*$"),
            self.h1_format
        ))

        # Heading 2 & 3: ## Subtitle
        self.highlighting_rules.append((
            QRegularExpression(r"^#{2,6}\s.*$"),
            self.h2_format
        ))

        # Bold: **bold**
        self.highlighting_rules.append((
            QRegularExpression(r"\*\*[^\*]+\*\*"),
            self.bold_format
        ))

        # Italic: *italic*
        self.highlighting_rules.append((
            QRegularExpression(r"(?<!\*)\*[^\*\n]+\*(?!\*)"),
            self.italic_format
        ))

        # Inline code: `code`
        self.highlighting_rules.append((
            QRegularExpression(r"`[^`\n]+`"),
            self.code_format
        ))

        # Checkboxes: - [ ] or - [x]
        self.highlighting_rules.append((
            QRegularExpression(r"^\s*-\s*\[[ xX]\]"),
            self.bullet_format
        ))

        # Bullet points: - or *
        self.highlighting_rules.append((
            QRegularExpression(r"^\s*[\*\-]\s"),
            self.bullet_format
        ))

        # Tables: |
        self.highlighting_rules.append((
            QRegularExpression(r"\|"),
            self.table_format
        ))

    def highlightBlock(self, text: str):
        """Apply syntax rules to current block."""
        for pattern, fmt in self.highlighting_rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)
