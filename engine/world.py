"""
World management with chunk system and procedural generation
"""
import numpy as np
try:
    import noise
    NOISE_AVAILABLE = True
except ImportError:
    NOISE_AVAILABLE = False
    
from settings import (
    WORLD_WIDTH, WORLD_HEIGHT, CHUNK_SIZE,
    SAND, WATER, LAVA, STONE, WOOD, FIRE, AIR, ICE
)


class Chunk:
    """Chunk quản lý một vùng của world"""
    
    def __init__(self, chunk_x, chunk_y, size=CHUNK_SIZE):
        self.chunk_x = chunk_x
        self.chunk_y = chunk_y
        self.size = size
        self.data = None  # Will be filled by World
        self.loaded = False
        self.modified = False
        
    def load(self, world_data):
        """Load chunk data from world grid"""
        start_x = self.chunk_x * self.size
        start_y = self.chunk_y * self.size
        end_x = min(start_x + self.size, world_data.shape[1])
        end_y = min(start_y + self.size, world_data.shape[0])
        
        self.data = world_data[start_y:end_y, start_x:end_x].copy()
        self.loaded = True
        
    def unload(self):
        """Unload chunk to save memory"""
        self.data = None
        self.loaded = False


class World:
    """Quản lý world với chunk system và procedural generation"""
    
    def __init__(self, width=WORLD_WIDTH, height=WORLD_HEIGHT, chunk_size=CHUNK_SIZE):
        self.width = width
        self.height = height
        self.chunk_size = chunk_size
        self.chunks = {}  # (chunk_x, chunk_y) -> Chunk
        
        # Create base grid
        self.grid = np.zeros((height, width), dtype=np.uint8)
        self.generated = False
        
        # Noise parameters for procedural generation
        self.seed = np.random.randint(0, 10000)
        self.terrain_scale = 0.02
        self.cave_scale = 0.05
        
    def generate_terrain(self):
        """Sinh terrain procedural bằng noise"""
        if not NOISE_AVAILABLE:
            self.generate_simple_terrain()
            return
            
        print(f"Generating terrain with seed {self.seed}...")
        
        # Generate heightmap
        heightmap = np.zeros((self.width,))
        for x in range(self.width):
            # Combine multiple octaves of noise
            n = noise.pnoise1(x * self.terrain_scale + self.seed, octaves=3, persistence=0.5, 
                             lacunarity=2.0)
            heightmap[x] = int((n + 1) / 2 * self.height * 0.6) + self.height * 0.2
            
        # Fill terrain
        for x in range(self.width):
            h = int(heightmap[x])
            for y in range(self.height):
                if y < h:
                    self.grid[y, x] = AIR
                elif y < h + 5:
                    self.grid[y, x] = SAND
                elif y < h + 20:
                    self.grid[y, x] = STONE
                else:
                    # Deep underground - maybe caves
                    cave_noise = noise.pnoise2((x + self.seed) * self.cave_scale, 
                                               (y + self.seed) * self.cave_scale,
                                               octaves=2, persistence=0.5)
                    if cave_noise > 0.6:
                        self.grid[y, x] = AIR
                    else:
                        self.grid[y, x] = STONE
                        
        # Add some water lakes
        for _ in range(5):
            lake_x = np.random.randint(0, self.width)
            lake_y = np.random.randint(int(self.height * 0.3), int(self.height * 0.7))
            lake_radius = np.random.randint(10, 30)
            
            for dy in range(-lake_radius, lake_radius + 1):
                for dx in range(-lake_radius, lake_radius + 1):
                    if dx*dx + dy*dy <= lake_radius*lake_radius:
                        x, y = lake_x + dx, lake_y + dy
                        if 0 <= x < self.width and 0 <= y < self.height:
                            if self.grid[y, x] in (STONE, SAND, AIR):
                                if y > int(heightmap[lake_x]):
                                    self.grid[y, x] = WATER
                                    
        # Add lava pools deep underground
        for _ in range(3):
            pool_x = np.random.randint(0, self.width)
            pool_y = np.random.randint(int(self.height * 0.7), int(self.height * 0.9))
            pool_radius = np.random.randint(5, 15)
            
            for dy in range(-pool_radius, pool_radius + 1):
                for dx in range(-pool_radius, pool_radius + 1):
                    if dx*dx + dy*dy <= pool_radius*pool_radius:
                        x, y = pool_x + dx, pool_y + dy
                        if 0 <= x < self.width and 0 <= y < self.height:
                            self.grid[y, x] = LAVA
                            
        # Add some wood/vegetation on surface
        for _ in range(20):
            tree_x = np.random.randint(0, self.width)
            tree_y = int(heightmap[tree_x]) - 1
            if 0 <= tree_y < self.height:
                # Simple tree
                for i in range(5):
                    if 0 <= tree_y - i < self.height:
                        self.grid[tree_y - i, tree_x] = WOOD
                        
        self.generated = True
        print("Terrain generation complete!")
        
    def generate_simple_terrain(self):
        """Simple terrain generation without noise library"""
        print("Generating simple terrain (noise library not available)...")
        
        # Create simple layered terrain
        for x in range(self.width):
            # Simple sine wave heightmap
            h = int(self.height * 0.4 + 20 * np.sin(x * 0.05))
            
            for y in range(self.height):
                if y < h:
                    self.grid[y, x] = AIR
                elif y < h + 5:
                    self.grid[y, x] = SAND
                elif y < h + 15:
                    self.grid[y, x] = STONE
                else:
                    self.grid[y, x] = STONE
                    
        # Add water layer
        water_level = int(self.height * 0.5)
        for x in range(self.width):
            for y in range(water_level, min(water_level + 10, self.height)):
                if self.grid[y, x] == AIR:
                    self.grid[y, x] = WATER
                    
        # Add lava deep
        lava_level = int(self.height * 0.8)
        for x in range(self.width // 3, 2 * self.width // 3):
            for y in range(lava_level, min(lava_level + 5, self.height)):
                self.grid[y, x] = LAVA
                
        self.generated = True
        
    def get_chunk(self, chunk_x, chunk_y):
        """Get or create chunk"""
        key = (chunk_x, chunk_y)
        if key not in self.chunks:
            chunk = Chunk(chunk_x, chunk_y, self.chunk_size)
            chunk.load(self.grid)
            self.chunks[key] = chunk
        return self.chunks[key]
        
    def set_pixel(self, x, y, material):
        """Set pixel and mark chunk as modified"""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.grid[y, x] = material
            # Mark chunk as modified
            chunk_x, chunk_y = x // self.chunk_size, y // self.chunk_size
            key = (chunk_x, chunk_y)
            if key in self.chunks:
                self.chunks[key].modified = True
                
    def get_pixel(self, x, y):
        """Get pixel value"""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[y, x]
        return AIR
        
    def unload_distant_chunks(self, player_chunk_x, player_chunk_y, max_distance=5):
        """Unload chunks far from player to save memory"""
        keys_to_remove = []
        for key, chunk in self.chunks.items():
            dist = abs(key[0] - player_chunk_x) + abs(key[1] - player_chunk_y)
            if dist > max_distance:
                chunk.unload()
                keys_to_remove.append(key)
                
        for key in keys_to_remove:
            del self.chunks[key]
            
    def get_visible_chunks(self, camera_x, camera_y, screen_width, screen_height):
        """Get chunks visible on screen"""
        tile_size = 4  # From settings
        start_chunk_x = int(camera_x / tile_size / self.chunk_size)
        start_chunk_y = int(camera_y / tile_size / self.chunk_size)
        end_chunk_x = int((camera_y + screen_height) / tile_size / self.chunk_size) + 1
        end_chunk_y = int((camera_y + screen_height) / tile_size / self.chunk_size) + 1
        
        visible = []
        for cy in range(start_chunk_y, end_chunk_y + 1):
            for cx in range(start_chunk_x, end_chunk_x + 1):
                if 0 <= cx < self.width // self.chunk_size and 0 <= cy < self.height // self.chunk_size:
                    visible.append(self.get_chunk(cx, cy))
                    
        return visible
