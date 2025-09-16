"""Terminal-based Minesweeper game implemented in Python.

This module provides a simple command line interface to play Minesweeper.
Users can choose the size of the board and the number of mines, then interact
with the game using textual commands to reveal or flag cells.
"""
from __future__ import annotations

import argparse
import random
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Tuple


@dataclass
class Cell:
    """Represents an individual cell on the Minesweeper board."""

    is_mine: bool = False
    is_revealed: bool = False
    is_flagged: bool = False
    adjacent_mines: int = 0


class MinesweeperGame:
    """Encapsulates the state and behaviour of a Minesweeper board."""

    def __init__(self, rows: int, cols: int, mines: int, *, seed: Optional[int] = None) -> None:
        if rows <= 0 or cols <= 0:
            raise ValueError("Rows and columns must both be positive integers.")
        if mines <= 0:
            raise ValueError("The number of mines must be a positive integer.")
        if mines >= rows * cols:
            raise ValueError("The number of mines must be less than the number of cells.")

        self.rows = rows
        self.cols = cols
        self.mines = mines
        self._random = random.Random(seed)
        self._board: List[List[Cell]] = [[Cell() for _ in range(cols)] for _ in range(rows)]
        self._mines_placed = False

    def reveal(self, row: int, col: int) -> bool:
        """Reveal the cell at ``(row, col)``.

        Returns ``True`` when the reveal succeeds without triggering a mine.
        Returns ``False`` if the revealed cell contains a mine.
        """

        self._validate_position(row, col)

        if not self._mines_placed:
            self._place_mines(exclude=(row, col))

        cell = self._board[row][col]
        if cell.is_flagged or cell.is_revealed:
            return True

        cell.is_revealed = True
        if cell.is_mine:
            return False

        if cell.adjacent_mines == 0:
            self._flood_reveal(row, col)

        return True

    def toggle_flag(self, row: int, col: int) -> None:
        """Toggle a flag on the cell at ``(row, col)``."""

        self._validate_position(row, col)
        cell = self._board[row][col]
        if cell.is_revealed:
            return
        cell.is_flagged = not cell.is_flagged

    def is_complete(self) -> bool:
        """Return ``True`` if all non-mine cells have been revealed."""

        return all(cell.is_revealed or cell.is_mine for row in self._board for cell in row)

    def count_flags(self) -> int:
        """Return the number of currently flagged cells."""

        return sum(1 for row in self._board for cell in row if cell.is_flagged)

    def board_as_strings(self, *, reveal_all: bool = False) -> List[List[str]]:
        """Return a textual representation of the board.

        Parameters
        ----------
        reveal_all:
            When ``True`` every non-mine cell is shown as if it were revealed and
            all mines are displayed. When ``False`` only the player's visible
            state is presented.
        """

        rendered: List[List[str]] = []
        for r in range(self.rows):
            row_chars: List[str] = []
            for c in range(self.cols):
                cell = self._board[r][c]
                if cell.is_mine and (cell.is_revealed or reveal_all):
                    row_chars.append("*")
                    continue

                visible = cell.is_revealed or (reveal_all and not cell.is_mine)
                if visible:
                    if cell.adjacent_mines > 0:
                        row_chars.append(str(cell.adjacent_mines))
                    else:
                        row_chars.append(" ")
                else:
                    row_chars.append("F" if cell.is_flagged else "#")
            rendered.append(row_chars)
        return rendered

    # ------------------------------------------------------------------
    # Internal helpers

    def _place_mines(self, exclude: Tuple[int, int]) -> None:
        """Randomly place mines on the board, avoiding ``exclude``."""

        available = [(r, c) for r in range(self.rows) for c in range(self.cols) if (r, c) != exclude]
        mine_positions = self._random.sample(available, self.mines)
        for r, c in mine_positions:
            self._board[r][c].is_mine = True
        self._compute_adjacent_counts()
        self._mines_placed = True

    def _compute_adjacent_counts(self) -> None:
        for r in range(self.rows):
            for c in range(self.cols):
                cell = self._board[r][c]
                if cell.is_mine:
                    cell.adjacent_mines = 0
                    continue
                cell.adjacent_mines = sum(1 for nr, nc in self._neighbors(r, c) if self._board[nr][nc].is_mine)

    def _flood_reveal(self, row: int, col: int) -> None:
        stack = [(row, col)]
        visited = set(stack)

        while stack:
            current_row, current_col = stack.pop()
            for nr, nc in self._neighbors(current_row, current_col):
                neighbor = self._board[nr][nc]
                if neighbor.is_revealed or neighbor.is_flagged or neighbor.is_mine:
                    continue

                neighbor.is_revealed = True
                if neighbor.adjacent_mines == 0 and (nr, nc) not in visited:
                    stack.append((nr, nc))
                    visited.add((nr, nc))

    def _neighbors(self, row: int, col: int) -> Iterable[Tuple[int, int]]:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = row + dr, col + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    yield nr, nc

    def _validate_position(self, row: int, col: int) -> None:
        if not (0 <= row < self.rows and 0 <= col < self.cols):
            raise ValueError(f"Position ({row + 1}, {col + 1}) is outside the board.")


def render_board(game: MinesweeperGame, *, reveal_all: bool = False) -> str:
    """Return a string that visually represents the board."""

    board = game.board_as_strings(reveal_all=reveal_all)
    cell_width = max(2, len(str(game.cols)))

    lines: List[str] = []
    header_cells = [f"{c + 1:>{cell_width}}" for c in range(game.cols)]
    lines.append(" " * 4 + " ".join(header_cells))

    for r, row in enumerate(board):
        line_cells = [f"{value:>{cell_width}}" for value in row]
        lines.append(f"{r + 1:>3} " + " ".join(line_cells))

    return "\n".join(lines)


def parse_command(text: str) -> Tuple[str, Optional[Tuple[int, int]]]:
    """Parse a user command into an action and coordinates."""

    tokens = text.strip().split()
    if not tokens:
        raise ValueError("Empty command. Use 'r row col' to reveal or 'f row col' to flag.")

    action = tokens[0].lower()
    if action in {"q", "quit", "exit"}:
        return ("quit", None)

    if action not in {"r", "reveal", "f", "flag"}:
        raise ValueError("Unknown command. Use 'r' to reveal, 'f' to flag, or 'q' to quit.")

    if len(tokens) != 3:
        raise ValueError("Commands must include row and column numbers, e.g. 'r 2 3'.")

    try:
        row = int(tokens[1])
        col = int(tokens[2])
    except ValueError as exc:  # pragma: no cover - simple user input validation
        raise ValueError("Row and column must be integers.") from exc

    return action[0], (row - 1, col - 1)


def run_game(game: MinesweeperGame) -> None:
    """Run the interactive game loop."""

    print("欢迎来到命令行扫雷！")
    print("使用指令 'r 行 列' 翻开格子，'f 行 列' 标记或取消标记雷，'q' 退出。")

    while True:
        print()
        print(render_board(game))
        print(f"已标记: {game.count_flags()} / {game.mines}")

        user_input = input("请输入指令: ")
        try:
            action, coords = parse_command(user_input)
        except ValueError as exc:
            print(f"输入无效: {exc}")
            continue

        if action == "quit":
            print("游戏已退出。")
            return

        if coords is None:
            print("输入无效: 缺少坐标。")
            continue

        row, col = coords
        try:
            if action == "r":
                success = game.reveal(row, col)
                if not success:
                    print("哦不，你踩到了地雷！")
                    print(render_board(game, reveal_all=True))
                    return
            else:
                game.toggle_flag(row, col)
        except ValueError as exc:
            print(f"输入无效: {exc}")
            continue

        if game.is_complete():
            print("恭喜你，成功排除了所有地雷！")
            print(render_board(game, reveal_all=True))
            return


def parse_args(args: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """Parse command line arguments."""

    parser = argparse.ArgumentParser(description="在终端里体验经典的扫雷游戏。")
    parser.add_argument("-r", "--rows", type=int, default=9, help="棋盘行数，默认为 9。")
    parser.add_argument("-c", "--cols", type=int, default=9, help="棋盘列数，默认为 9。")
    parser.add_argument("-m", "--mines", type=int, default=10, help="地雷数量，默认为 10。")
    parser.add_argument("--seed", type=int, default=None, help="随机种子，用于重现相同的棋盘。")
    return parser.parse_args(args)


def main() -> None:
    arguments = parse_args()
    try:
        game = MinesweeperGame(arguments.rows, arguments.cols, arguments.mines, seed=arguments.seed)
    except ValueError as exc:
        raise SystemExit(str(exc))

    run_game(game)


if __name__ == "__main__":
    main()
