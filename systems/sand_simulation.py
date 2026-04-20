"""
Sand simulation system - optimized falling sand physics
This is the core simulation engine for pixel-based physics
"""
import numpy as np
from settings import (
    WORLD_WIDTH, WORLD_HEIGHT, GRAVITY, LIQUID_FLOW_SPEED,
    FIRE_SPREAD_CHANCE, AIR, SAND, WATER, LAVA, STONE, WOOD,
    FIRE, SMOKE, ASH, ACID, ICE, MATERIAL_PROPS, REACTIONS
)


class SandSimulation:
    """
    Optimized falling sand simulation với NumPy
    Handles all pixel-based physics interactions
    """
    
    def __init__(self, width=WORLD_WIDTH, height=WORLD_HEIGHT):
        self.width = width
        self.height = height
        
        # Main simulation grids
        self.grid = np.zeros((height, width), dtype=np.uint8)
        self.temperature = np.full((height, width), 20, dtype=np.float32)  # Room temp
        self.lifetime = np.zeros((height, width), dtype=np.int16)
        self.velocity_x = np.zeros((height, width), dtype=np.float32)
        self.velocity_y = np.zeros((height, width), dtype=np.float32)
        
        # Optimization: track active cells
        self.active_cells = set()
        self.max_active_cells = width * height // 4  # Limit active cells
        
    def set_pixel(self, x, y, material, lifetime=0):
        """Set a pixel with optional lifetime"""
        if 0 <= x < self.width and 0 <= y < self.height:
            old_mat = self.grid[y, x]
            self.grid[y, x] = material
            self.lifetime[y, x] = lifetime
            
            # Add to active cells
            if material != AIR:
                self.active_cells.add((x, y))
                
    def get_pixel(self, x, y):
        """Get pixel material"""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[y, x]
        return AIR
        
    def clear_pixel(self, x, y):
        """Clear a pixel (set to air)"""
        self.set_pixel(x, y, AIR, 0)
        
    def explode(self, cx, cy, radius):
        """Create explosion at position"""
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if dx*dx + dy*dy <= radius*radius:
                    x, y = cx + dx, cy + dy
                    if 0 <= x < self.width and 0 <= y < self.height:
                        self.grid[y, x] = AIR
                        self.lifetime[y, x] = 0
                        
                        # Add fire in center
                        if dx*dx + dy*dy <= (radius // 2)**2:
                            if np.random.random() < 0.4:
                                self.set_pixel(x, y, FIRE, 30)
                                
    def update_region(self, start_x, start_y, end_x, end_y):
        """Update simulation in a specific region (for chunk-based updates)"""
        start_x = max(0, start_x)
        start_y = max(0, start_y)
        end_x = min(self.width, end_x)
        end_y = min(self.height, end_y)
        
        # Create views of the region
        region = self.grid[start_y:end_y, start_x:end_x].copy()
        lifetime_region = self.lifetime[start_y:end_y, start_x:end_x].copy()
        
        # Process from bottom to top for gravity
        for y in range(region.shape[0] - 1, -1, -1):
            alt_y = start_y + y
            # Alternate direction to prevent bias
            if y % 2 == 0:
                x_range = range(region.shape[1])
            else:
                x_range = range(region.shape[1] - 1, -1, -1)
                
            for x in x_range:
                alt_x = start_x + x
                mat = region[y, x]
                
                if mat == AIR or mat == STONE:
                    continue
                    
                props = MATERIAL_PROPS.get(mat, {})
                
                # Handle lifetime
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
                    if y < region.shape[0] - 1:
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
                                if 0 <= nx < region.shape[1]:
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
                    if y < region.shape[0] - 1:
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
                                    if 0 <= nx < region.shape[1]:
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
        
    def update_reactions(self, start_x, start_y, end_x, end_y):
        """Process chemical reactions in region"""
        start_x = max(0, start_x)
        start_y = max(0, start_y)
        end_x = min(self.width, end_x)
        end_y = min(self.height, end_y)
        
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                mat = self.grid[y, x]
                if mat == AIR:
                    continue
                    
                # Check neighbors for reactions
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        if dx == 0 and dy == 0:
                            continue
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < self.width and 0 <= ny < self.height:
                            neighbor = self.grid[ny, nx]
                            
                            # Check reaction table
                            if (mat, neighbor) in REACTIONS:
                                result = REACTIONS[(mat, neighbor)]
                                self.grid[y, x] = result
                                self.grid[ny, nx] = result
                                
                                # Spawn smoke
                                if np.random.random() < 0.3:
                                    smoke_y = y - 1
                                    if 0 <= smoke_y < self.height:
                                        self.set_pixel(nx, smoke_y, SMOKE, 60)
                                        
                            elif (neighbor, mat) in REACTIONS:
                                result = REACTIONS[(neighbor, mat)]
                                self.grid[y, x] = result
                                self.grid[ny, nx] = result
                                
                # Fire spread
                if mat == FIRE:
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < self.width and 0 <= ny < self.height:
                                neighbor = self.grid[ny, nx]
                                neighbor_props = MATERIAL_PROPS.get(neighbor, {})
                                if neighbor_props.get('flammable', False):
                                    if np.random.random() < FIRE_SPREAD_CHANCE:
                                        self.set_pixel(nx, ny, FIRE, 30)
                                        
                # Acid erosion
                if mat == ACID:
                    for dy in [0, 1]:
                        for dx in [-1, 0, 1]:
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < self.width and 0 <= ny < self.height:
                                neighbor = self.grid[ny, nx]
                                if neighbor in (STONE, WOOD, ICE):
                                    if np.random.random() < 0.15:
                                        self.clear_pixel(nx, ny)
                                        
    def update(self, player_x=None, player_y=None, update_radius=100):
        """
        Main update function với optimization
        If player position provided, only update area near player
        """
        if player_x is not None and player_y is not None:
            # Only update region around player
            start_x = max(0, int(player_x) - update_radius)
            start_y = max(0, int(player_y) - update_radius)
            end_x = min(self.width, int(player_x) + update_radius)
            end_y = min(self.height, int(player_y) + update_radius)
            
            self.update_region(start_x, start_y, end_x, end_y)
            self.update_reactions(start_x, start_y, end_x, end_y)
        else:
            # Full update (slower)
            self.update_region(0, 0, self.width, self.height)
            self.update_reactions(0, 0, self.width, self.height)
            
    def fill_circle(self, cx, cy, radius, material):
        """Fill circle with material"""
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if dx*dx + dy*dy <= radius*radius:
                    x, y = cx + dx, cy + dy
                    if 0 <= x < self.width and 0 <= y < self.height:
                        self.set_pixel(x, y, material)
                        
    def get_material_count(self, material):
        """Count pixels of a material"""
        return np.sum(self.grid == material)
        
    def get_statistics(self):
        """Get simulation statistics"""
        stats = {}
        for mat_id in range(11):
            count = self.get_material_count(mat_id)
            if count > 0:
                stats[MATERIAL_PROPS.get(mat_id, {}).get('name', str(mat_id))] = count
        return stats
