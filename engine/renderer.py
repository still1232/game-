"""
Renderer module - handles all rendering operations
Uses pygame for pixel-based rendering with batch optimization
Optimized with sprite sheets and GPU-accelerated rendering
"""
import pygame
import numpy as np
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE, WORLD_WIDTH, WORLD_HEIGHT,
    MATERIAL_PROPS, AIR, UPDATE_RADIUS
)
import os


class AssetManager:
    """Manages all game assets (sprites, tilesets)"""
    
    def __init__(self):
        self.sprites = {}
        self.tilesets = {}
        self.material_textures = {}
        self.asset_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets')
        
    def load_tileset(self, filename, tile_size=16):
        """Load a tileset and split into individual tiles"""
        filepath = os.path.join(self.asset_dir, filename)
        if not os.path.exists(filepath):
            return None
            
        try:
            image = pygame.image.load(filepath).convert_alpha()
        except:
            return None
            
        tiles = []
        rows = image.get_height() // tile_size
        cols = image.get_width() // tile_size
        
        for row in range(rows):
            for col in range(cols):
                rect = pygame.Rect(col * tile_size, row * tile_size, tile_size, tile_size)
                tile = image.subsurface(rect).copy()
                # Scale to TILE_SIZE
                tile = pygame.transform.scale(tile, (TILE_SIZE, TILE_SIZE))
                tiles.append(tile)
                
        self.tilesets[filename] = tiles
        return tiles
    
    def load_sprite(self, filename, name):
        """Load a sprite sheet"""
        filepath = os.path.join(self.asset_dir, filename)
        if not os.path.exists(filepath):
            return None
            
        try:
            image = pygame.image.load(filepath).convert_alpha()
            self.sprites[name] = image
            return image
        except:
            return None
    
    def get_material_texture(self, mat_id):
        """Get texture for a material"""
        if mat_id in self.material_textures:
            return self.material_textures[mat_id]
            
        props = MATERIAL_PROPS.get(mat_id, {})
        texture_rect = props.get('texture_rect')
        
        if texture_rect and 'roguelike_pack.png' in self.tilesets:
            tileset = self.tilesets['roguelike_pack.png']
            tile_index = (texture_rect[1] // 16) * (1024 // 16) + (texture_rect[0] // 16)
            if 0 <= tile_index < len(tileset):
                self.material_textures[mat_id] = tileset[tile_index]
                return tileset[tile_index]
        
        # Fallback: create colored surface
        color = props.get('color', (255, 255, 255))
        surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
        surf.fill(color[:3])
        self.material_textures[mat_id] = surf
        return surf


class Renderer:
    """Render engine với batch rendering và camera system - OPTIMIZED"""
    
    def __init__(self, screen_width=SCREEN_WIDTH, screen_height=SCREEN_HEIGHT, tile_size=TILE_SIZE):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.tile_size = tile_size
        
        # Initialize pygame surface
        self.screen = pygame.display.set_mode((screen_width, screen_height), pygame.DOUBLEBUF)
        pygame.display.set_caption("Noita-like Pixel Physics Game - Optimized")
        
        # Asset manager
        self.assets = AssetManager()
        self._load_assets()
        
        # Camera
        self.camera_x = 0
        self.camera_y = 0
        self.shake_offset = (0, 0)
        self.shake_timer = 0
        
        # Pre-compute material textures
        self.material_textures = {}
        for mat_id in MATERIAL_PROPS.keys():
            self.material_textures[mat_id] = self.assets.get_material_texture(mat_id)
        
        # Create render surface for batch rendering
        self.render_surface = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        
        # Lighting overlay
        self.light_surface = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        
        # Particle system for effects
        self.particles = []
        
        # Optimization: cache visible rects
        self.last_visible_range = None
        
    def _load_assets(self):
        """Load all assets"""
        self.assets.load_tileset('tileset.png', 16)
        self.assets.load_tileset('cave_tileset.png', 16)
        # Player and enemy sprites will use fallback colored rectangles if not found
        self.assets.load_sprite('player_sprite.png', 'player')
        self.assets.load_sprite('enemy_sprite.png', 'enemy')
        
    def set_camera(self, x, y, world_width=WORLD_WIDTH, world_height=WORLD_HEIGHT):
        """Set camera position with bounds checking - smooth follow"""
        max_x = max(0, world_width * self.tile_size - self.screen_width)
        max_y = max(0, world_height * self.tile_size - self.screen_height)
        
        # Smooth camera follow
        target_x = max(0, min(x - self.screen_width // 2, max_x))
        target_y = max(0, min(y - self.screen_height // 2, max_y))
        
        self.camera_x += (target_x - self.camera_x) * 0.1
        self.camera_y += (target_y - self.camera_y) * 0.1
        
    def add_shake(self, intensity=10, duration=10):
        """Add camera shake effect"""
        self.shake_offset = (intensity, intensity)
        self.shake_timer = duration
        
    def update_shake(self):
        """Update shake effect"""
        if self.shake_timer > 0:
            self.shake_timer -= 1
            if self.shake_timer <= 0:
                self.shake_offset = (0, 0)
                
    def world_to_screen(self, wx, wy):
        """Convert world coordinates to screen coordinates"""
        sx = int(wx * self.tile_size - self.camera_x)
        sy = int(wy * self.tile_size - self.camera_y)
        
        # Apply shake
        if self.shake_timer > 0:
            import random
            sx += random.randint(-self.shake_offset[0], self.shake_offset[0])
            sy += random.randint(-self.shake_offset[1], self.shake_offset[1])
            
        return sx, sy
        
    def screen_to_world(self, sx, sy):
        """Convert screen coordinates to world coordinates"""
        wx = int((sx + self.camera_x) / self.tile_size)
        wy = int((sy + self.camera_y) / self.tile_size)
        return wx, wy
    
    def _calculate_visible_range(self, player_x, player_y, pixel_world):
        """Calculate optimized visible range based on player position"""
        # Only update area around player
        margin = UPDATE_RADIUS // self.tile_size + 2
        
        start_x = max(0, int(player_x) - margin)
        start_y = max(0, int(player_y) - margin)
        end_x = min(pixel_world.width, int(player_x) + margin)
        end_y = min(pixel_world.height, int(player_y) + margin)
        
        return start_x, start_y, end_x, end_y
        
    def render_world_optimized(self, pixel_world, player_x, player_y):
        """
        OPTIMIZED: Render only visible area around player
        Uses batch rendering with pre-computed surfaces
        """
        # Calculate visible range
        visible_range = self._calculate_visible_range(player_x, player_y, pixel_world)
        start_x, start_y, end_x, end_y = visible_range
        
        # Clear screen
        self.screen.fill((20, 20, 35))  # Dark background
        
        # Get grid slice for visible area
        grid_slice = pixel_world.grid[start_y:end_y, start_x:end_x].copy()
        
        # Batch render by material type - OPTIMIZED with numpy
        for mat_id, texture in self.material_textures.items():
            if mat_id == AIR:
                continue
                
            # Find positions of this material using numpy
            mask = grid_slice == mat_id
            if not mask.any():
                continue
            
            # Get coordinates efficiently
            positions = np.argwhere(mask)
            
            # Batch blit for this material
            for py, px in positions:
                wx = start_x + px
                wy = start_y + py
                sx, sy = self.world_to_screen(wx, wy)
                
                # Only render if on screen
                if -TILE_SIZE <= sx < self.screen_width and -TILE_SIZE <= sy < self.screen_height:
                    self.screen.blit(texture, (sx, sy))
        
        self.last_visible_range = visible_range
        
    def render_entity(self, entity):
        """Render an entity with sprite support"""
        if not entity.visible:
            return
            
        sprite = entity.get_sprite()
        if sprite is not None:
            sx, sy = self.world_to_screen(entity.x, entity.y)
            
            # Check if on screen
            if (-sprite.get_width() <= sx < self.screen_width and 
                -sprite.get_height() <= sy < self.screen_height):
                self.screen.blit(sprite, (sx, sy))
        else:
            # Fallback: draw rectangle
            rect = entity.get_rect()
            sx, sy = self.world_to_screen(rect.x, rect.y)
            pygame.draw.rect(self.screen, entity.color, 
                           (sx, sy, rect.width * self.tile_size, rect.height * self.tile_size))
            
    def add_particle(self, particle):
        """Add particle effect"""
        if len(self.particles) < 500:  # Limit particles
            self.particles.append(particle)
        
    def render_particles(self):
        """Render and update particles - OPTIMIZED"""
        i = 0
        while i < len(self.particles):
            p = self.particles[i]
            p.update()
            
            if p.is_alive():
                sx, sy = self.world_to_screen(p.x, p.y)
                
                # Only render if on screen
                if 0 <= sx < self.screen_width and 0 <= sy < self.screen_height:
                    p.render(self.screen, sx, sy)
                i += 1
            else:
                self.particles.pop(i)
                
    def render_lighting(self, light_sources):
        """Simple 2D lighting system - OPTIMIZED"""
        self.light_surface.fill((0, 0, 0, 180))
        
        for light in light_sources:
            lx, ly, radius, intensity = light
            sx, sy = self.world_to_screen(lx, ly)
            
            # Optimized gradient
            for r in range(int(radius), 0, -5):
                alpha = min(255, int(intensity * (r / radius) * 100))
                color = (255, 255, 200, alpha)
                pygame.draw.circle(self.light_surface, color, (sx, sy), r)
        
        # Apply lighting with blend
        self.screen.blit(self.light_surface, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
        
    def render_ui(self, ui_elements):
        """Render UI elements"""
        font = pygame.font.Font(None, 24)
        
        for element in ui_elements:
            element.render(self.screen)
        
        # FPS counter
        fps_text = font.render(f"FPS: {int(pygame.time.Clock().get_fps())}", True, (255, 255, 255))
        self.screen.blit(fps_text, (10, 10))
            
    def flip(self):
        """Update display"""
        pygame.display.flip()
        
    def clear(self):
        """Clear screen"""
        self.screen.fill((0, 0, 0))


class Particle:
    """Simple particle for effects"""
    
    def __init__(self, x, y, vx, vy, color, lifetime=30, size=4):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.size = size
        
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.2
        self.lifetime -= 1
        
    def is_alive(self):
        return self.lifetime > 0
        
    def render(self, screen, sx, sy):
        alpha = int(255 * (self.lifetime / self.max_lifetime))
        color = (*self.color[:3], alpha)
        s = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        pygame.draw.circle(s, color, (self.size//2, self.size//2), self.size//2)
        screen.blit(s, (sx, sy))
