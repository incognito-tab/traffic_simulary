"""
Intersection GUI – renders the traffic grid using tkinter.
Replaces IntersectionForm.cs + IntersectionForm.Designer.cs (WinForms).
"""

import tkinter as tk
import utils
import colorsys


# Pre-computed color palette for cars
_CAR_COLORS = []
for i in range(utils.NO_CARS):
    hue = (i * 0.618033988749895) % 1.0  # golden ratio for nice distribution
    r, g, b = colorsys.hsv_to_rgb(hue, 0.7, 0.9)
    _CAR_COLORS.append(f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}")


class IntersectionGUI:
    """tkinter-based GUI for the traffic simulation grid."""

    def __init__(self):
        self._owner_agent = None
        self._root: tk.Tk = None
        self._canvas: tk.Canvas = None
        self._ready = False

    def set_owner(self, agent):
        self._owner_agent = agent

    def create_window(self):
        """Create the tkinter window (must be called from the GUI thread)."""
        self._root = tk.Tk()
        self._root.title("Traffic Simulator")
        self._root.geometry("620x640")
        self._root.configure(bg="#1a1a2e")

        self._canvas = tk.Canvas(self._root, bg="#16213e", highlightthickness=0)
        self._canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self._canvas.bind("<Configure>", lambda e: self._draw_intersection())

        self._ready = True
        self._root.mainloop()

    def update_gui(self):
        """Schedule a redraw on the tkinter main thread."""
        if self._ready and self._root:
            try:
                self._root.after(0, self._draw_intersection)
            except tk.TclError:
                pass  # Window was closed

    def _pick_color(self, value: int) -> str:
        """Pick a color for a car based on its ID."""
        idx = value % len(_CAR_COLORS)
        return _CAR_COLORS[idx]

    def _draw_intersection(self):
        """Redraw the entire grid, traffic lights, and cars."""
        if not self._canvas or not self._ready:
            return

        self._canvas.delete("all")

        w = self._canvas.winfo_width()
        h = self._canvas.winfo_height()
        if w < 10 or h < 10:
            return

        min_xy = min(w, h)
        cell_size = (min_xy - 40) // utils.SIZE
        offset_base = 20

        # ── Draw grid lines ───────────────────────────────────────
        for i in range(utils.SIZE + 1):
            # Horizontal
            self._canvas.create_line(
                offset_base, offset_base + i * cell_size,
                offset_base + utils.SIZE * cell_size, offset_base + i * cell_size,
                fill="#2a2a4a", width=1
            )
            # Vertical
            self._canvas.create_line(
                offset_base + i * cell_size, offset_base,
                offset_base + i * cell_size, offset_base + utils.SIZE * cell_size,
                fill="#2a2a4a", width=1
            )

        if not self._owner_agent:
            return

        # ── Draw unavailable cells (black) ────────────────────────
        for j in range(1, utils.SIZE - 1, 2):
            for i in range(1, utils.SIZE - 1, 2):
                x1 = offset_base + i * cell_size
                y1 = offset_base + j * cell_size
                self._canvas.create_rectangle(
                    x1, y1, x1 + cell_size, y1 + cell_size,
                    fill="#0f0f23", outline="#0f0f23"
                )

        # ── Draw traffic lights ───────────────────────────────────
        for tl_data in self._owner_agent.traffic_light_positions.values():
            tx = int(tl_data[0])
            ty = int(tl_data[1])
            state = utils.TrafficLightState(tl_data[2])

            if state == utils.TrafficLightState.Green:
                b1_color = "#00e676"  # vertical green
                b2_color = "#ff1744"  # horizontal red
            else:
                b1_color = "#ff1744"  # vertical red
                b2_color = "#00e676"  # horizontal green

            bar_w = max(cell_size // 10, 2)

            # Vertical bars (left and right edges)
            x1 = offset_base + tx * cell_size
            y1 = offset_base + ty * cell_size
            self._canvas.create_rectangle(
                x1, y1, x1 + bar_w, y1 + cell_size,
                fill=b2_color, outline=b2_color
            )
            self._canvas.create_rectangle(
                x1 + cell_size, y1, x1 + cell_size + bar_w, y1 + cell_size,
                fill=b2_color, outline=b2_color
            )

            # Horizontal bars (top and bottom edges)
            self._canvas.create_rectangle(
                x1, y1, x1 + cell_size, y1 + bar_w,
                fill=b1_color, outline=b1_color
            )
            self._canvas.create_rectangle(
                x1, y1 + cell_size, x1 + cell_size, y1 + cell_size + bar_w,
                fill=b1_color, outline=b1_color
            )

        # ── Draw starting points ──────────────────────────────────
        labels = ["A", "B", "C", "D"]
        for i in range(utils.NO_STARTING_POINTS):
            x1 = offset_base + (i * 2) * cell_size
            y1 = offset_base + utils.SIZE * cell_size
            self._canvas.create_rectangle(
                x1, y1, x1 + cell_size, y1 + cell_size,
                fill="#4a6fa5", outline="#5a7fb5"
            )
            label = labels[i] if i < len(labels) else str(i)
            self._canvas.create_text(
                x1 + cell_size // 2, y1 + cell_size // 2,
                text=label, fill="white",
                font=("Arial", max(cell_size // 4, 8), "bold")
            )

        # ── Draw destination labels ───────────────────────────────
        dest_labels = ["M", "N", "O", "P"]
        for i in range(utils.NO_STARTING_POINTS):
            x1 = offset_base + (i * 2) * cell_size
            y1 = offset_base - cell_size
            if y1 >= 0:
                self._canvas.create_rectangle(
                    x1, y1, x1 + cell_size, y1 + cell_size,
                    fill="#3a5f45", outline="#4a7055"
                )
                label = dest_labels[i] if i < len(dest_labels) else str(i)
                self._canvas.create_text(
                    x1 + cell_size // 2, y1 + cell_size // 2,
                    text=label, fill="white",
                    font=("Arial", max(cell_size // 4, 8), "bold")
                )

        # ── Draw cars ─────────────────────────────────────────────
        nr_cars_per_cell = [0] * (utils.SIZE * utils.SIZE + 1)

        for car_data in self._owner_agent.car_positions.values():
            cx = int(car_data[0])
            cy = int(car_data[1])
            car_id_str = car_data[2]
            car_id_int = int(car_id_str)

            cell_idx = cx * utils.SIZE + cy
            if cell_idx < 0 or cell_idx >= len(nr_cars_per_cell):
                continue

            nr_count = nr_cars_per_cell[cell_idx]

            if 0 < nr_count < utils.MAX_NO_CARS_PER_CELL:
                ox = (nr_count // utils.NO_CARS_PER_CELL) * (cell_size // utils.NO_CARS_PER_CELL)
                oy = (nr_count % utils.NO_CARS_PER_CELL) * (cell_size // utils.NO_CARS_PER_CELL)
            else:
                ox = 0
                oy = 0

            sub_size = cell_size // utils.NO_CARS_PER_CELL
            rx = offset_base + cx * cell_size + ox
            ry = offset_base + cy * cell_size + oy

            color = self._pick_color(car_id_int)
            self._canvas.create_rectangle(
                rx, ry, rx + sub_size, ry + sub_size,
                fill=color, outline="#ffffff", width=1
            )
            # Car ID text
            font_size = max(sub_size // 3, 6)
            self._canvas.create_text(
                rx + sub_size // 2, ry + sub_size // 2,
                text=car_id_str, fill="black",
                font=("Arial", font_size, "bold")
            )

            nr_cars_per_cell[cell_idx] += 1
