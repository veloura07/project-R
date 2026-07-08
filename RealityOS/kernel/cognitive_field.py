"""
cognitive_field.py — 2D Reaction-Diffusion Cognitive Field solver for Project S.

Implements Step 8.5 of the Phase 0 roadmap:
    - 2D grid discretizing configuration space
    - Explicit Euler finite-difference solver for reaction-diffusion (Laplacian stencil)
    - Source injection from CEs
    - Bilinear value interpolation and central-difference gradient lookup (g = -grad(phi))
"""

import math
from typing import List, Tuple, Dict, Any


class CognitiveField2D:
    """
    A 2D spatial cognitive field (e.g. Risk, Goal, Curiosity) evolving over
    a configuration space Ω using a discretised reaction-diffusion PDE.
    """

    def __init__(
        self,
        name: str,
        width: int = 40,
        height: int = 40,
        dx: float = 0.5,
        diffusion_rate: float = 0.1,    # D_phi
        decay_rate: float = 0.05,       # gamma (dissipation / reaction term)
    ):
        self.name = name
        self.width = width
        self.height = height
        self.dx = dx
        self.diffusion_rate = diffusion_rate
        self.decay_rate = decay_rate

        # Initialize the 2D grid with zeros
        self.grid = [[0.0 for _ in range(height)] for _ in range(width)]
        self.next_grid = [[0.0 for _ in range(height)] for _ in range(width)]
        
        # Sources: (x_pos, y_pos) -> rate
        self.sources: Dict[Tuple[int, int], float] = {}

    def set_source(self, grid_x: int, grid_y: int, strength: float):
        """Set or update emitter source strength at a specific grid coordinate."""
        if 0 <= grid_x < self.width and 0 <= grid_y < self.height:
            self.sources[(grid_x, grid_y)] = strength

    def clear_sources(self):
        self.sources.clear()

    def step(self, dt: float = 0.05):
        """
        Evolve the field one step using explicit Euler integration:
        phi(t+1) = phi(t) + dt * (D_phi * Laplacian(phi) - decay * phi + S_phi)
        """
        dx2 = self.dx ** 2

        for i in range(self.width):
            for j in range(self.height):
                # 1. Compute Laplacian using 5-point stencil with boundary padding (zero-flux / clamp)
                left  = self.grid[i - 1][j] if i > 0 else self.grid[0][j]
                right = self.grid[i + 1][j] if i < self.width - 1 else self.grid[self.width - 1][j]
                down  = self.grid[i][j - 1] if j > 0 else self.grid[i][0]
                up    = self.grid[i][j + 1] if j < self.height - 1 else self.grid[i][self.height - 1]
                center = self.grid[i][j]

                laplacian = (left + right + down + up - 4.0 * center) / dx2

                # 2. Source term
                source = self.sources.get((i, j), 0.0)

                # 3. Euler step
                diff = self.diffusion_rate * laplacian
                reaction = -self.decay_rate * center
                
                self.next_grid[i][j] = center + dt * (diff + reaction + source)

        # Swap buffers
        self.grid, self.next_grid = self.next_grid, self.grid

    def world_to_grid(self, x: float, y: float) -> Tuple[float, float]:
        """Convert continuous coordinate space to grid float index."""
        grid_x = x / self.dx
        grid_y = y / self.dx
        return grid_x, grid_y

    def value_at(self, x: float, y: float) -> float:
        """Bilinear interpolation of the field strength at continuous pos (x, y)."""
        gx, gy = self.world_to_grid(x, y)
        
        # Clamp to bounds
        gx = max(0.0, min(self.width - 1.001, gx))
        gy = max(0.0, min(self.height - 1.001, gy))

        x0 = int(gx)
        x1 = x0 + 1
        y0 = int(gy)
        y1 = y0 + 1

        tx = gx - x0
        ty = gy - y0

        # Bilinear interpolation
        c00 = self.grid[x0][y0]
        c10 = self.grid[x1][y0]
        c01 = self.grid[x0][y1]
        c11 = self.grid[x1][y1]

        v = (
            c00 * (1 - tx) * (1 - ty) +
            c10 * tx * (1 - ty) +
            c01 * (1 - tx) * ty +
            c11 * tx * ty
        )
        return v

    def gradient_at(self, x: float, y: float) -> Tuple[float, float]:
        """
        Compute central finite-difference gradient of the field.
        Force g = -grad(phi) will pull CEs along the steepest ascent path.
        """
        step = self.dx * 0.5
        val_xp = self.value_at(x + step, y)
        val_xn = self.value_at(x - step, y)
        val_yp = self.value_at(x, y + step)
        val_yn = self.value_at(x, y - step)

        grad_x = (val_xp - val_xn) / (2.0 * step)
        grad_y = (val_yp - val_yn) / (2.0 * step)

        return grad_x, grad_y
