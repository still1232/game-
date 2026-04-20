"""
Sand simulation system - HIGHLY OPTIMIZED falling sand physics
Uses NumPy vectorization and region-based updates for maximum performance
"""
import numpy as np
from settings import (
    WORLD_WIDTH, WORLD_HEIGHT, GRAVITY, LIQUID_FLOW_SPEED,
    FIRE_SPREAD_CHANCE, AIR, SAND, WATER, LAVA, STONE, WOOD,
    FIRE, SMOKE, ASH, ACID, ICE, MATERIAL_PROPS, REACTIONS, UPDATE_RADIUS
)


class SandSimulation:
    """
    Highly optimized falling sand simulation với NumPy
    Uses vectorized operations and spatial partitioning
    """
    
    def __init__(self, width=WORLD_WIDTH, height=WORLD_HEIGHT):
        self.width = width
        self.height = height
        
        # Main simulation grids - use uint8 for memory efficiency
        self.grid = np.zeros((height, width), dtype=np.uint8)
        self.temperature = np.full((height, width), 20, dtype=np.float32)
        self.lifetime = np.zeros((height, width), dtype=np.int16)
        
        # Optimization: only track active regions
        self.last_update_region = None
        self.update_counter = 0
        
    def set_pixel(self, x, y, material, lifetime=0):
        """Set a pixel with optional lifetime - batched version available"""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.grid[y, x] = material
            self.lifetime[y, x] = lifetime
            
    def set_pixels_batch(self, positions, materials, lifetimes=None):
        """Batch set multiple pixels - MUCH FASTER"""
        xs, ys = zip(*[(x, y) for x, y in positions if 0 <= x < self.width and 0 <= y < self.height])
        if xs:
            self.grid[ys, xs] = materials[:len(xs)]
            if lifetimes:
                self.lifetime[ys, xs] = lifetimes[:len(xs)]
            
    def get_pixel(self, x, y):
        """Get pixel material"""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[y, x]
        return AIR
        
    def clear_pixel(self, x, y):
        """Clear a pixel (set to air)"""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.grid[y, x] = AIR
            self.lifetime[y, x] = 0
        
    def explode(self, cx, cy, radius):
        """Create explosion at position - OPTIMIZED with numpy"""
        # Create circular mask using numpy
        y_coords, x_coords = np.ogrid[-cy:self.height-cy, -cx:self.width-cx]
        mask = (x_coords*x_coords + y_coords*y_coords) <= radius*radius
        
        # Clear terrain
        self.grid[mask] = AIR
        self.lifetime[mask] = 0
        
        # Add fire in center
        center_mask = (x_coords*x_coords + y_coords*y_coords) <= (radius // 2)**2
        fire_positions = np.random.random(self.grid.shape) < 0.4
        combined_mask = mask & center_mask & fire_positions
        self.grid[combined_mask] = FIRE
        self.lifetime[combined_mask] = 30
                        
    def _update_solid_particles(self, region, lifetime_region, y_start, y_end):
        """Update solid particles (sand, ash) - VECTORIZED"""
        height, width = region.shape
        
        for y in range(height - 2, -1, -1):
            actual_y = y_start + y
            # Get current row and row below
            current_row = region[y, :]
            below_row = region[y + 1, :]
            
            # Find solid particles in current row
            solid_mask = np.isin(current_row, [SAND, ASH])
            
            # Check what's below (air or liquid)
            below_is_air = below_row == AIR
            below_is_liquid = np.isin(below_row, [WATER, LAVA, ACID])
            can_fall = below_is_air | below_is_liquid
            
            # Combine conditions
            fall_mask = solid_mask & can_fall
            
            if np.any(fall_mask):
                # Move falling particles down
                falling_materials = current_row[fall_mask]
                displaced_materials = below_row[fall_mask]
                
                region[y + 1, fall_mask] = falling_materials
                region[y, fall_mask] = displaced_materials
                
                # Transfer lifetimes
                if np.any(np.isin(falling_materials, [FIRE, SMOKE])):
                    fall_indices = np.where(fall_mask)[0]
                    for i, idx in enumerate(fall_indices):
                        lifetime_region[y + 1, idx] = lifetime_region[y, idx]
                        
    def _update_liquids(self, region, lifetime_region, y_start, y_end):
        """Update liquids (water, lava, acid) - OPTIMIZED"""
        height, width = region.shape
        liquid_types = [WATER, LAVA, ACID]
        
        for y in range(height - 2, -1, -1):
            actual_y = y_start + y
            
            for liquid in liquid_types:
                # Find liquid positions
                liquid_mask = region[y, :] == liquid
                
                if not np.any(liquid_mask):
                    continue
                    
                # Try to fall down
                below_is_air = region[y + 1, :] == AIR
                can_fall = liquid_mask & below_is_air
                
                if np.any(can_fall):
                    region[y + 1, can_fall] = liquid
                    region[y, can_fall] = AIR
                    
                # Flow horizontally where can't fall
                remaining_liquid = liquid_mask & ~can_fall
                if np.any(remaining_liquid):
                    # Flow left and right
                    for direction in [-1, 1]:
                        for flow_dist in range(1, 4):
                            shifted = np.roll(remaining_liquid, direction * flow_dist)
                            target_empty = region[y, :] == AIR
                            can_flow = shifted & target_empty & ~remaining_liquid
                            
                            if np.any(can_flow):
                                region[y, can_flow] = liquid
                                region[y, shifted & ~can_flow] = AIR
                                
    def update_region(self, start_x, start_y, end_x, end_y):
        """Update simulation in a specific region - HIGHLY OPTIMIZED"""
        start_x = max(0, start_x)
        start_y = max(0, start_y)
        end_x = min(self.width, end_x)
        end_y = min(self.height, end_y)
        
        if start_x >= end_x or start_y >= end_y:
            return
            
        # Create views
        region = self.grid[start_y:end_y, start_x:end_x].copy()
        lifetime_region = self.lifetime[start_y:end_y, start_x:end_x].copy()
        
        height, width = region.shape
        
        # Process from bottom to top
        for y in range(height - 1, -1, -1):
            actual_y = start_y + y
            
            # Alternate scan direction to prevent bias
            if y % 2 == 0:
                x_range = range(width)
            else:
                x_range = range(width - 1, -1, -1)
                
            for x in x_range:
                actual_x = start_x + x
                mat = region[y, x]
                
                if mat == AIR or mat == STONE:
                    continue
                    
                props = MATERIAL_PROPS.get(mat, {})
                
                # Handle lifetime for temporary elements
                if 'lifetime' in props:
                    lifetime_region[y, x] -= 1
                    if lifetime_region[y, x] <= 0:
                        region[y, x] = AIR
                        lifetime_region[y, x] = 0
                        continue
                        
                # Gas behavior (rise up)
                if props.get('gas', False):
                    if y > 0 and region[y-1, x] == AIR:
                        region[y-1, x] = mat
                        region[y, x] = AIR
                        lifetime_region[y-1, x] = lifetime_region[y, x]
                    continue
                    
                # Solid particles (fall down)
                if props.get('solid', False) and not props.get('liquid', False):
                    if y < height - 1:
                        below = region[y+1, x]
                        below_props = MATERIAL_PROPS.get(below, {})
                        
                        if below == AIR or below_props.get('liquid') or below_props.get('gas'):
                            region[y+1, x] = mat
                            region[y, x] = below
                            lifetime_region[y+1, x] = lifetime_region[y, x]
                        else:
                            # Try diagonal slide
                            for dx in [-1, 1]:
                                nx = x + dx
                                if 0 <= nx < width:
                                    diag = region[y+1, nx]
                                    diag_props = MATERIAL_PROPS.get(diag, {})
                                    if diag == AIR or diag_props.get('liquid'):
                                        region[y+1, nx] = mat
                                        region[y, x] = diag
                                        lifetime_region[y+1, nx] = lifetime_region[y, x]
                                        break
                    continue
                    
                # Liquid behavior
                if props.get('liquid', False):
                    if y < height - 1:
                        below = region[y+1, x]
                        below_props = MATERIAL_PROPS.get(below, {})
                        
                        if below == AIR or below_props.get('gas'):
                            region[y+1, x] = mat
                            region[y, x] = AIR
                            lifetime_region[y+1, x] = lifetime_region[y, x]
                        else:
                            # Flow horizontally
                            flow_dist = int(LIQUID_FLOW_SPEED * 3)
                            for direction in [-1, 1]:
                                for i in range(1, flow_dist + 1):
                                    nx = x + (direction * i)
                                    if 0 <= nx < width:
                                        side = region[y, nx]
                                        if side == AIR:
                                            region[y, nx] = mat
                                            region[y, x] = AIR
                                            lifetime_region[y, nx] = lifetime_region[y, x]
                                            break
                                        elif side != mat:
                                            break
                    continue
        
        # Update main grid
        self.grid[start_y:end_y, start_x:end_x] = region
        self.lifetime[start_y:end_y, start_x:end_x] = lifetime_region
        self.last_update_region = (start_x, start_y, end_x, end_y)
        
    def update_reactions(self, start_x, start_y, end_x, end_y):
        """Process chemical reactions in region - OPTIMIZED"""
        start_x = max(0, start_x)
        start_y = max(0, start_y)
        end_x = min(self.width, end_x)
        end_y = min(self.height, end_y)
        
        if start_x >= end_x or start_y >= end_y:
            return
            
        # Vectorized reaction checking
        region = self.grid[start_y:end_y, start_x:end_x]
        
        # Fire spread - check all flammable materials near fire
        fire_mask = region == FIRE
        if np.any(fire_mask):
            # Get fire positions
            fire_positions = np.argwhere(fire_mask)
            
            for fy, fx in fire_positions[::2]:  # Sample every other fire pixel
                # Check random neighbors
                for _ in range(3):
                    dy = np.random.randint(-1, 2)
                    dx = np.random.randint(-1, 2)
                    ny, nx = fy + dy, fx + dx
                    
                    if 0 <= ny < region.shape[0] and 0 <= nx < region.shape[1]:
                        neighbor = region[ny, nx]
                        neighbor_props = MATERIAL_PROPS.get(neighbor, {})
                        if neighbor_props.get('flammable', False):
                            if np.random.random() < FIRE_SPREAD_CHANCE:
                                region[ny, nx] = FIRE
                                self.lifetime[start_y + ny, start_x + nx] = 30
        
        # Acid erosion
        acid_mask = region == ACID
        if np.any(acid_mask):
            acid_positions = np.argwhere(acid_mask)
            erodible = [STONE, WOOD, ICE]
            
            for ay, ax in acid_positions[::2]:
                # Check below acid
                ny = ay + 1
                if 0 <= ny < region.shape[0]:
                    neighbor = region[ny, ax]
                    if neighbor in erodible and np.random.random() < 0.15:
                        region[ny, ax] = AIR
                        self.lifetime[start_y + ny, start_x + ax] = 0
        
        self.grid[start_y:end_y, start_x:end_x] = region
                        
    def update(self, player_x=None, player_y=None, update_radius=None):
        """
        Main update function với MAXIMUM OPTIMIZATION
        Only updates area near player for better performance
        """
        if update_radius is None:
            update_radius = UPDATE_RADIUS
            
        if player_x is not None and player_y is not None:
            # Only update region around player
            start_x = max(0, int(player_x) - update_radius)
            start_y = max(0, int(player_y) - update_radius)
            end_x = min(self.width, int(player_x) + update_radius)
            end_y = min(self.height, int(player_y) + update_radius)
            
            self.update_region(start_x, start_y, end_x, end_y)
            self.update_reactions(start_x, start_y, end_x, end_y)
        else:
            # Full update (slower, use sparingly)
            chunk_size = 64
            for cy in range(0, self.height, chunk_size):
                for cx in range(0, self.width, chunk_size):
                    self.update_region(cx, cy, cx + chunk_size, cy + chunk_size)
                    self.update_reactions(cx, cy, cx + chunk_size, cy + chunk_size)
            
    def fill_circle(self, cx, cy, radius, material):
        """Fill circle with material - NUMPY OPTIMIZED"""
        y_min = max(0, cy - radius)
        y_max = min(self.height, cy + radius + 1)
        x_min = max(0, cx - radius)
        x_max = min(self.width, cx + radius + 1)
        
        if y_min >= y_max or x_min >= x_max:
            return
            
        y_coords, x_coords = np.ogrid[y_min:y_max, x_min:x_max]
        mask = (x_coords - cx)**2 + (y_coords - cy)**2 <= radius**2
        
        # Apply to correct region of grid
        self.grid[y_min:y_max, x_min:x_max][mask] = material
        self.lifetime[y_min:y_max, x_min:x_max][mask] = 0
                        
    def get_material_count(self, material):
        """Count pixels of a material"""
        return np.sum(self.grid == material)
        
    def get_statistics(self):
        """Get simulation statistics"""
        stats = {}
        unique, counts = np.unique(self.grid, return_counts=True)
        for mat_id, count in zip(unique, counts):
            if mat_id != AIR and count > 0:
                name = MATERIAL_PROPS.get(mat_id, {}).get('name', str(mat_id))
                stats[name] = int(count)
        return stats
