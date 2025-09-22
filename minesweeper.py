"""命令行扫雷游戏。

这个版本提供以下特性：

* 首次翻开必定安全，地雷会在第一次操作后才布置。
* 支持翻开、插旗与取消插旗操作。
* 以 1 为起点的坐标，更符合日常使用习惯。
* 通过清晰的中文提示引导玩家进行游戏。

运行 ``python minesweeper.py`` 即可开始游戏。
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple


@dataclass
class Cell:
    """棋盘上的一个格子。"""

    has_mine: bool = False
    opened: bool = False
    flagged: bool = False
    adjacent: int = 0

    def display(self, *, reveal_all: bool = False) -> str:
        """返回用于展示的字符。"""

        if reveal_all:
            if self.has_mine:
                return "*"
            if self.adjacent:
                return str(self.adjacent)
            return " "

        if self.flagged and not self.opened:
            return "F"
        if not self.opened:
            return "□"
        if self.has_mine:
            return "*"
        if self.adjacent:
            return str(self.adjacent)
        return " "


class Minesweeper:
    """封装扫雷棋盘和玩法逻辑。"""

    def __init__(self, rows: int, cols: int, mines: int) -> None:
        if rows <= 0 or cols <= 0:
            raise ValueError("行列数必须为正整数。")
        if not (1 <= mines < rows * cols):
            raise ValueError("地雷数量必须介于 1 和 行×列-1 之间。")

        self.rows = rows
        self.cols = cols
        self.mine_total = mines
        self._grid: List[List[Cell]] = [[Cell() for _ in range(cols)] for _ in range(rows)]
        self._mines_placed = False

    # -- 初始化与邻居辅助 -------------------------------------------------
    def _neighbours(self, row: int, col: int) -> Iterable[Tuple[int, int]]:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                r, c = row + dr, col + dc
                if 0 <= r < self.rows and 0 <= c < self.cols:
                    yield r, c

    def _place_mines(self, safe_cell: Tuple[int, int]) -> None:
        """在首次翻开之后布置地雷，确保首掀格安全。"""

        safe_row, safe_col = safe_cell
        candidates = [
            (r, c)
            for r in range(self.rows)
            for c in range(self.cols)
            if (r, c) != (safe_row, safe_col)
        ]
        random.shuffle(candidates)
        for r, c in candidates[: self.mine_total]:
            self._grid[r][c].has_mine = True

        for r in range(self.rows):
            for c in range(self.cols):
                cell = self._grid[r][c]
                if cell.has_mine:
                    cell.adjacent = -1
                else:
                    cell.adjacent = sum(
                        1 for nr, nc in self._neighbours(r, c) if self._grid[nr][nc].has_mine
                    )
        self._mines_placed = True

    def _ensure_mines(self, row: int, col: int) -> None:
        if not self._mines_placed:
            self._place_mines((row, col))

    # -- 基础操作 ---------------------------------------------------------
    def toggle_flag(self, row: int, col: int) -> None:
        self._ensure_mines(row, col)
        cell = self._grid[row][col]
        if cell.opened:
            return
        cell.flagged = not cell.flagged

    def open_cell(self, row: int, col: int) -> bool:
        """翻开格子。若踩雷返回 ``False``，否则返回 ``True``。"""

        self._ensure_mines(row, col)
        cell = self._grid[row][col]
        if cell.flagged or cell.opened:
            return True

        cell.opened = True
        if cell.has_mine:
            return False

        if cell.adjacent == 0:
            for nr, nc in self._neighbours(row, col):
                if not self._grid[nr][nc].opened:
                    self.open_cell(nr, nc)
        return True

    def reveal_all(self) -> None:
        for row in self._grid:
            for cell in row:
                cell.opened = True

    def all_safe_cells_opened(self) -> bool:
        return all(cell.opened or cell.has_mine for row in self._grid for cell in row)

    # -- 展示 --------------------------------------------------------------
    def render(self, *, reveal_all: bool = False) -> str:
        header_numbers = " ".join(f"{c:2d}" for c in range(1, self.cols + 1))
        horizontal = "    " + "―" * (3 * self.cols - 1)
        lines = ["    " + header_numbers, horizontal]
        for idx, row in enumerate(self._grid, start=1):
            body = " ".join(cell.display(reveal_all=reveal_all) for cell in row)
            lines.append(f"{idx:2d} | {body}")
        return "\n".join(lines)


# -- 用户交互 --------------------------------------------------------------
def ask_for_configuration() -> Tuple[int, int, int]:
    """向用户询问棋盘设置。"""

    print("请输入棋盘配置（行 列 地雷数），直接回车使用默认 9 9 10。")
    while True:
        raw = input("配置: ").strip()
        if not raw:
            return 9, 9, 10
        try:
            rows_str, cols_str, mines_str = raw.split()
            rows, cols, mines = int(rows_str), int(cols_str), int(mines_str)
        except ValueError:
            print("格式错误，请输入三个整数，例如：9 9 10。")
            continue
        if rows <= 0 or cols <= 0:
            print("行列数必须大于 0。")
            continue
        if not (1 <= mines < rows * cols):
            print("地雷数必须介于 1 和 行×列-1 之间。")
            continue
        return rows, cols, mines


def parse_command(command: str) -> Optional[Tuple[str, int, int]]:
    """解析玩家输入。返回 (操作, 行, 列)。"""

    tokens = command.strip().lower().split()
    if not tokens:
        return None

    if tokens[0] in {"r", "f"} and len(tokens) == 3:
        action = tokens[0]
        try:
            row = int(tokens[1])
            col = int(tokens[2])
        except ValueError:
            return None
        return action, row, col

    if len(tokens) == 2:
        try:
            row = int(tokens[0])
            col = int(tokens[1])
        except ValueError:
            return None
        return "r", row, col

    return None


def play() -> None:
    rows, cols, mines = ask_for_configuration()
    game = Minesweeper(rows, cols, mines)
    print(
        "游戏开始！输入指令：\n"
        "  r 行 列  —— 翻开格子（可简写为直接输入 行 列）\n"
        "  f 行 列  —— 插旗或取消旗帜\n"
        "  q        —— 退出游戏\n"
    )

    while True:
        print(game.render())
        command = input("你的操作: ").strip()
        if command.lower() == "q":
            print("你选择了退出游戏，再见！")
            return

        parsed = parse_command(command)
        if parsed is None:
            print("无法识别的指令，请重新输入，例如：r 3 4 或 f 5 6。")
            continue

        action, row_input, col_input = parsed
        row = row_input - 1
        col = col_input - 1
        if not (0 <= row < rows and 0 <= col < cols):
            print("坐标越界，请输入有效的行列号（从 1 开始）。")
            continue

        if action == "f":
            game.toggle_flag(row, col)
            continue

        alive = game.open_cell(row, col)
        if not alive:
            game.reveal_all()
            print(game.render(reveal_all=True))
            print("很遗憾，你踩到了地雷！")
            return

        if game.all_safe_cells_opened():
            game.reveal_all()
            print(game.render(reveal_all=True))
            print("恭喜你，成功排除所有地雷！")
            return


def main() -> None:
    try:
        play()
    except KeyboardInterrupt:
        print("\n游戏被中断，欢迎下次再来！")


if __name__ == "__main__":
    main()
