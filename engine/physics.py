"""
Physics engine for pixel-based simulation
Handles falling sand, liquid flow, fire spread, and material reactions
"""
import numpy as np
from settings import (
    WORLD_WIDTH, WORLD_HEIGHT, GRAVITY, LIQUID_FLOW_SPEED,
    FIRE_SPREAD_CHANCE, AIR, SAND, WATER, LAVA, STONE, WOOD,
    FIRE, SMOKE, ASH, ACID, ICE, MATERIAL_PROPS, REACTIONS
)


class PixelWorld:
    """Quản lý world dạng pixel với simulation falling sand"""
    
    def __init__(self, width=WORLD_WIDTH, height=WORLD_HEIGHT):
        self.width = width
        self.height = height
        # Grid chứa material ID
        self.grid = np.zeros((height, width), dtype=np.uint8)
        # Temperature grid
        self.temperature = np.zeros((height, width), dtype=np.float32)
        # Lifetime cho các particle có thời gian sống (fire, smoke)
        self.lifetime = np.zeros((height, width), dtype=np.int16)
        # Active regions để tối ưu update
        self.active_regions = set()
        
    def get_pixel(self, x, y):
        """Lấy material tại vị trí (x, y)"""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[y, x]
        return AIR
    
    def set_pixel(self, x, y, material, lifetime=0):
        """Đặt material tại vị trí (x, y)"""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.grid[y, x] = material
            self.lifetime[y, x] = lifetime
            # Đánh dấu vùng active
            cx, cy = x // 16, y // 16
            self.active_regions.add((cx, cy))
            
    def clear_pixel(self, x, y):
        """Xóa pixel (đặt thành air)"""
        self.set_pixel(x, y, AIR, 0)
        
    def explode(self, center_x, center_y, radius):
        """Tạo explosion, phá hủy terrain trong bán kính"""
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if dx*dx + dy*dy <= radius*radius:
                    x, y = center_x + dx, center_y + dy
                    if 0 <= x < self.width and 0 <= y < self.height:
                        # Tạo crater
                        self.grid[y, x] = AIR
                        self.lifetime[y, x] = 0
                        # Thêm fire ở tâm
                        if dx*dx + dy*dy <= (radius//2)**2:
                            if np.random.random() < 0.3:
                                self.set_pixel(x, y, FIRE, 30)
                                
    def update(self):
        """Update toàn bộ simulation - optimized version"""
        # Copy grid để tránh modify trong khi iterate
        new_grid = self.grid.copy()
        new_lifetime = self.lifetime.copy()
        
        # Update từ dưới lên trên để xử lý gravity đúng
        for y in range(self.height - 1, -1, -1):
            # Xử lý xen kẽ trái-phải để tránh bias
            direction = 1 if y % 2 == 0 else -1
            x_range = range(0, self.width) if direction == 1 else range(self.width - 1, -1, -1)
            
            for x in x_range:
                material = self.grid[y, x]
                
                if material == AIR or material == STONE or material == ICE:
                    continue
                    
                props = MATERIAL_PROPS.get(material, {})
                
                # Xử lý lifetime
                if 'lifetime' in props:
                    new_lifetime[y, x] -= 1
                    if new_lifetime[y, x] <= 0:
                        new_grid[y, x] = AIR
                        new_lifetime[y, x] = 0
                        continue
                
                # Xử lý gas (bay lên)
                if props.get('gas', False):
                    if y > 0 and self.grid[y-1, x] == AIR:
                        new_grid[y-1, x] = material
                        new_grid[y, x] = AIR
                        new_lifetime[y-1, x] = new_lifetime[y, x]
                    elif y > 0 and self.grid[y-1, x] != AIR:
                        # Try move sideways
                        side_x = x + (1 if x % 2 == 0 else -1)
                        if 0 <= side_x < self.width and self.grid[y, side_x] == AIR:
                            new_grid[y, side_x] = material
                            new_grid[y, x] = AIR
                    continue
                
                # Xử lý solid particles (falling sand)
                if props.get('solid', False) and not props.get('liquid', False):
                    if y < self.height - 1:
                        below = self.grid[y+1, x]
                        below_props = MATERIAL_PROPS.get(below, {})
                        
                        # Rơi xuống nếu là air hoặc liquid/gas nhẹ hơn
                        if below == AIR or below_props.get('liquid', False) or below_props.get('gas', False):
                            new_grid[y+1, x] = material
                            new_grid[y, x] = below
                            new_lifetime[y+1, x] = new_lifetime[y, x]
                        # Slide xuống chéo
                        elif y < self.height - 1:
                            slide_dirs = [-1, 1] if x % 2 == 0 else [1, -1]
                            for dx in slide_dirs:
                                nx = x + dx
                                if 0 <= nx < self.width:
                                    diag = self.grid[y+1, nx]
                                    diag_props = MATERIAL_PROPS.get(diag, {})
                                    if diag == AIR or diag_props.get('liquid', False):
                                        new_grid[y+1, nx] = material
                                        new_grid[y, x] = diag
                                        new_lifetime[y+1, nx] = new_lifetime[y, x]
                                        break
                    continue
                
                # Xử lý liquids
                if props.get('liquid', False):
                    if y < self.height - 1:
                        below = self.grid[y+1, x]
                        below_props = MATERIAL_PROPS.get(below, {})
                        
                        # Chảy xuống
                        if below == AIR or below_props.get('gas', False):
                            new_grid[y+1, x] = material
                            new_grid[y, x] = AIR
                            new_lifetime[y+1, x] = new_lifetime[y, x]
                        # Lan sang ngang
                        elif below not in (AIR, material):
                            flow_speed = int(LIQUID_FLOW_SPEED * 3)
                            for dir in [-1, 1]:
                                for i in range(1, flow_speed + 1):
                                    nx = x + (dir * i)
                                    if 0 <= nx < self.width:
                                        side = self.grid[y, nx]
                                        if side == AIR:
                                            new_grid[y, nx] = material
                                            new_grid[y, x] = AIR
                                            new_lifetime[y, nx] = new_lifetime[y, x]
                                            break
                                        elif side != material:
                                            break
                    continue
        
        # Xử lý reactions
        for y in range(self.height):
            for x in range(self.width):
                mat = new_grid[y, x]
                if mat == AIR:
                    continue
                    
                # Check neighbors for reactions
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        if dx == 0 and dy == 0:
                            continue
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < self.width and 0 <= ny < self.height:
                            neighbor = new_grid[ny, nx]
                            reaction_key = (mat, neighbor)
                            if reaction_key in REACTIONS:
                                result = REACTIONS[reaction_key]
                                new_grid[y, x] = result
                                new_grid[ny, nx] = result
                                # Tạo smoke
                                if np.random.random() < 0.3:
                                    smoke_y = y - 1
                                    if 0 <= smoke_y < self.height:
                                        new_grid[smoke_y, x] = SMOKE
                                        new_lifetime[smoke_y, x] = 60
                            elif (neighbor, mat) in REACTIONS:
                                result = REACTIONS[(neighbor, mat)]
                                new_grid[y, x] = result
                                new_grid[ny, nx] = result
                                
                # Fire spread
                if mat == FIRE:
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < self.width and 0 <= ny < self.height:
                                neighbor = new_grid[ny, nx]
                                neighbor_props = MATERIAL_PROPS.get(neighbor, {})
                                if neighbor_props.get('flammable', False):
                                    if np.random.random() < FIRE_SPREAD_CHANCE:
                                        new_grid[ny, nx] = FIRE
                                        new_lifetime[ny, nx] = 30
                                        # Tạo smoke
                                        if np.random.random() < 0.5:
                                            smoke_y = ny - 1
                                            if 0 <= smoke_y < self.height:
                                                new_grid[smoke_y, nx] = SMOKE
                                                new_lifetime[smoke_y, nx] = 60
                                                
                # Acid erosion
                if mat == ACID:
                    for dy in [0, 1]:
                        for dx in [-1, 0, 1]:
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < self.width and 0 <= ny < self.height:
                                neighbor = new_grid[ny, nx]
                                if neighbor in (STONE, WOOD, ICE):
                                    if np.random.random() < 0.1:
                                        new_grid[ny, nx] = AIR
                                        
        self.grid = new_grid
        self.lifetime = new_lifetime
        
    def get_chunk(self, chunk_x, chunk_y, size=16):
        """Lấy dữ liệu chunk"""
        start_x = chunk_x * size
        start_y = chunk_y * size
        end_x = min(start_x + size, self.width)
        end_y = min(start_y + size, self.height)
        return self.grid[start_y:end_y, start_x:end_x]
        
    def fill_circle(self, center_x, center_y, radius, material):
        """Điền circle với material"""
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if dx*dx + dy*dy <= radius*radius:
                    x, y = center_x + dx, center_y + dy
                    if 0 <= x < self.width and 0 <= y < self.height:
                        self.set_pixel(x, y, material)
