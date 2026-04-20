"""
Renderer module - handles all rendering operations
Uses pygame for pixel-based rendering with batch optimization
"""
import pygame
import numpy as np
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE, WORLD_WIDTH, WORLD_HEIGHT,
    MATERIAL_PROPS, AIR
)


class Renderer:
    """Render engine với batch rendering và camera system"""
    
    def __init__(self, screen_width=SCREEN_WIDTH, screen_height=SCREEN_HEIGHT, tile_size=TILE_SIZE):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.tile_size = tile_size
        
        # Initialize pygame surface
        self.screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("Noita-like Pixel Physics Game")
        
        # Camera
        self.camera_x = 0
        self.camera_y = 0
        self.shake_offset = (0, 0)
        self.shake_timer = 0
        
        # Create material color lookup table (optimized)
        self.color_table = {}
        for mat_id, props in MATERIAL_PROPS.items():
            color = props.get('color', (255, 255, 255, 255))
            self.color_table[mat_id] = pygame.Color(*color)
            
        # Pre-create surfaces for each material type (batch rendering)
        self.material_surfaces = {}
        for mat_id, color in self.color_table.items():
            if mat_id != AIR:
                surf = pygame.Surface((tile_size, tile_size))
                surf.fill(color[:3])  # RGB only
                self.material_surfaces[mat_id] = surf
                
        # Lighting overlay
        self.light_surface = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        
        # Particle system for effects
        self.particles = []
        
    def set_camera(self, x, y, world_width=WORLD_WIDTH, world_height=WORLD_HEIGHT):
        """Set camera position with bounds checking"""
        max_x = max(0, world_width * self.tile_size - self.screen_width)
        max_y = max(0, world_height * self.tile_size - self.screen_height)
        self.camera_x = max(0, min(x, max_x))
        self.camera_y = max(0, min(y, max_y))
        
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
        
    def render_world(self, pixel_world, visible_range=None):
        """
        Render pixel world với optimized batch rendering
        visible_range: (start_x, start_y, end_x, end_y) trong world coordinates
        """
        if visible_range is None:
            # Calculate visible range based on camera
            start_x = max(0, int(self.camera_x / self.tile_size) - 1)
            start_y = max(0, int(self.camera_y / self.tile_size) - 1)
            end_x = min(pixel_world.width, start_x + int(self.screen_width / self.tile_size) + 2)
            end_y = min(pixel_world.height, start_y + int(self.screen_height / self.tile_size) + 2)
        else:
            start_x, start_y, end_x, end_y = visible_range
            
        # Clear screen
        self.screen.fill((0, 0, 0))
        
        # Batch render pixels
        # Create a temporary surface for the visible area
        visible_width = end_x - start_x
        visible_height = end_y - start_y
        
        if visible_width <= 0 or visible_height <= 0:
            return
            
        # Direct pixel drawing (optimized with numpy)
        grid_slice = pixel_world.grid[start_y:end_y, start_x:end_x]
        
        # Draw each material type
        for mat_id, surface in self.material_surfaces.items():
            if mat_id == AIR:
                continue
            # Find all positions of this material
            mask = grid_slice == mat_id
            if not mask.any():
                continue
                
            # Get coordinates
            ys, xs = np.where(mask)
            for y, x in zip(ys, xs):
                wx = start_x + x
                wy = start_y + y
                sx, sy = self.world_to_screen(wx, wy)
                self.screen.blit(surface, (sx, sy))
                
    def render_entity(self, entity):
        """Render an entity (player, enemy, etc.)"""
        if not entity.visible:
            return
            
        sprite = entity.get_sprite()
        if sprite is None:
            # Fallback: draw rectangle
            rect = entity.get_rect()
            sx, sy = self.world_to_screen(rect.x, rect.y)
            pygame.draw.rect(self.screen, entity.color, 
                           (sx, sy, rect.width * self.tile_size, rect.height * self.tile_size))
        else:
            sx, sy = self.world_to_screen(entity.x, entity.y)
            self.screen.blit(sprite, (sx, sy))
            
    def add_particle(self, particle):
        """Add particle effect"""
        self.particles.append(particle)
        
    def render_particles(self):
        """Render and update particles"""
        i = 0
        while i < len(self.particles):
            p = self.particles[i]
            p.update()
            if p.is_alive():
                sx, sy = self.world_to_screen(p.x, p.y)
                p.render(self.screen, sx, sy)
                i += 1
            else:
                self.particles.pop(i)
                
    def render_lighting(self, light_sources):
        """Simple 2D lighting system"""
        self.light_surface.fill((0, 0, 0, 200))  # Dark overlay
        
        for light in light_sources:
            lx, ly, radius, intensity = light
            sx, sy = self.world_to_screen(lx, ly)
            
            # Create gradient circle
            for r in range(radius, 0, -3):
                alpha = int(intensity * (r / radius))
                color = (255, 255, 200, alpha)
                pygame.draw.circle(self.light_surface, color, (sx, sy), r)
                
        # Apply lighting
        self.screen.blit(self.light_surface, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
        
    def render_ui(self, ui_elements):
        """Render UI elements (HP bar, etc.)"""
        for element in ui_elements:
            element.render(self.screen)
            
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
        self.vy += 0.2  # Gravity
        self.lifetime -= 1
        
    def is_alive(self):
        return self.lifetime > 0
        
    def render(self, screen, sx, sy):
        alpha = int(255 * (self.lifetime / self.max_lifetime))
        color = (*self.color[:3], alpha)
        s = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        pygame.draw.circle(s, color, (self.size//2, self.size//2), self.size//2)
        screen.blit(s, (sx, sy))
