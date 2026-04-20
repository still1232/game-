import pygame
import os

pygame.init()

os.makedirs('assets', exist_ok=True)

# Tạo player sprite đẹp hơn (pixel art style)
def create_player_sprite():
    size = 16
    frames = 8
    surface = pygame.Surface((size * frames, size), pygame.SRCALPHA)
    
    colors = {
        'skin': (255, 220, 180),
        'hair': (100, 60, 30),
        'shirt': (180, 50, 50),
        'pants': (50, 50, 120),
        'boot': (40, 30, 20),
        'eye': (255, 255, 255),
        'pupil': (0, 0, 0)
    }
    
    for frame in range(frames):
        offset_x = frame * size
        bob = 1 if frame % 4 == 0 else 0
        
        # Body
        pygame.draw.rect(surface, colors['shirt'], (offset_x + 4, 5 + bob, 8, 5))
        pygame.draw.rect(surface, colors['pants'], (offset_x + 4, 10 + bob, 8, 4))
        
        # Head
        pygame.draw.rect(surface, colors['skin'], (offset_x + 4, 1 + bob, 8, 5))
        pygame.draw.rect(surface, colors['hair'], (offset_x + 4, 1 + bob, 8, 2))
        
        # Eyes
        eye_dir = 1 if frame % 8 < 4 else -1
        pygame.draw.rect(surface, colors['eye'], (offset_x + 5 + eye_dir, 3 + bob, 2, 2))
        pygame.draw.rect(surface, colors['pupil'], (offset_x + 5 + eye_dir, 3 + bob, 1, 1))
        
        # Legs animation
        leg_offset = 1 if frame % 4 == 1 or frame % 4 == 3 else 0
        pygame.draw.rect(surface, colors['boot'], (offset_x + 4, 14 + bob, 3, 2))
        pygame.draw.rect(surface, colors['boot'], (offset_x + 9 - leg_offset, 14 + bob, 3, 2))
    
    pygame.image.save(surface, 'assets/player_sprite.png')
    print("Created player_sprite.png")

# Tạo slime enemy sprite
def create_slime_sprite():
    size = 16
    frames = 6
    surface = pygame.Surface((size * frames, size), pygame.SRCALPHA)
    
    slime_green = (80, 180, 80)
    slime_dark = (50, 120, 50)
    slime_light = (120, 220, 120)
    
    for frame in range(frames):
        offset_x = frame * size
        squash = frame % 3
        width = 12 + (squash - 1) * 2
        height = 10 - (squash - 1)
        start_x = offset_x + (size - width) // 2
        start_y = 16 - height - 2
        
        # Main body (ellipse-like using rectangles)
        for y in range(height):
            w = max(4, width - abs(y - height//2) * 2)
            x = start_x + (width - w) // 2
            color = slime_light if y < 3 else slime_green if y < height-2 else slime_dark
            pygame.draw.rect(surface, color, (x, start_y + y, w, 1))
        
        # Eyes
        eye_y = start_y + 3
        pygame.draw.rect(surface, (255, 255, 255), (start_x + 3, eye_y, 3, 3))
        pygame.draw.rect(surface, (255, 255, 255), (start_x + width - 6, eye_y, 3, 3))
        pygame.draw.rect(surface, (0, 0, 0), (start_x + 4, eye_y + 1, 1, 1))
        pygame.draw.rect(surface, (0, 0, 0), (start_x + width - 5, eye_y + 1, 1, 1))
    
    pygame.image.save(surface, 'assets/enemy_slime.png')
    print("Created enemy_slime.png")

# Tạo fly enemy sprite
def create_fly_sprite():
    size = 16
    frames = 4
    surface = pygame.Surface((size * frames, size * 2), pygame.SRCALPHA)
    
    body_color = (40, 40, 40)
    wing_color = (200, 200, 255, 150)
    eye_color = (200, 50, 50)
    
    for frame in range(frames):
        offset_x = frame * size
        wing_up = frame % 2 == 0
        
        # Body
        pygame.draw.ellipse(surface, body_color, (offset_x + 5, 8, 6, 5))
        
        # Wings
        if wing_up:
            pygame.draw.ellipse(surface, wing_color, (offset_x + 2, 4, 5, 6))
            pygame.draw.ellipse(surface, wing_color, (offset_x + 9, 4, 5, 6))
        else:
            pygame.draw.ellipse(surface, wing_color, (offset_x + 2, 8, 5, 4))
            pygame.draw.ellipse(surface, wing_color, (offset_x + 9, 8, 5, 4))
        
        # Eyes
        pygame.draw.circle(surface, eye_color, (offset_x + 7, 10), 2)
        pygame.draw.circle(surface, eye_color, (offset_x + 9, 10), 2)
    
    pygame.image.save(surface, 'assets/enemy_fly.png')
    print("Created enemy_fly.png")

# Tạo particle sprite sheet
def create_particles():
    size = 8
    frames = 8
    surface = pygame.Surface((size * frames, size), pygame.SRCALPHA)
    
    colors = [(255, 200, 50), (255, 150, 50), (255, 100, 50), (255, 50, 50),
              (200, 50, 50), (150, 50, 50), (100, 50, 50), (50, 50, 50)]
    
    for frame in range(frames):
        offset_x = frame * size
        alpha = 255 - frame * 30
        color = (*colors[frame % len(colors)][:3], alpha)
        
        # Draw particle with glow effect
        for i in range(3):
            s = size - i * 2
            c = (max(0, color[0] - i*20), max(0, color[1] - i*20), max(0, color[2] - i*20), max(0, alpha - i*50))
            surf = pygame.Surface((s, s), pygame.SRCALPHA)
            pygame.draw.circle(surf, c, (s//2, s//2), s//2)
            surface.blit(surf, (offset_x + i, i))
    
    pygame.image.save(surface, 'assets/particles.png')
    print("Created particles.png")

# Tạo tileset cave
def create_tileset():
    tile_size = 16
    tiles_x, tiles_y = 16, 10
    surface = pygame.Surface((tile_size * tiles_x, tile_size * tiles_y))
    
    # Colors for different tiles
    dirt = (101, 67, 33)
    dirt_dark = (81, 53, 26)
    stone = (128, 128, 128)
    stone_dark = (100, 100, 100)
    grass = (76, 153, 76)
    grass_dark = (51, 102, 51)
    
    for y in range(tiles_y):
        for x in range(tiles_x):
            rect = (x * tile_size, y * tile_size, tile_size, tile_size)
            
            # Create varied terrain
            if y < 2:
                # Sky/empty (transparent handled separately)
                pygame.draw.rect(surface, (50, 50, 80), rect)
            elif y < 4:
                # Grass layer
                base = grass if (x + y) % 3 == 0 else grass_dark
                pygame.draw.rect(surface, base, rect)
                # Add some grass detail
                if (x * y) % 5 == 0:
                    pygame.draw.line(surface, (100, 180, 100), 
                                   (x * tile_size + 4, y * tile_size),
                                   (x * tile_size + 4, y * tile_size + 4), 2)
            elif y < 7:
                # Dirt layer
                base = dirt if (x + y) % 2 == 0 else dirt_dark
                pygame.draw.rect(surface, base, rect)
                # Add pebbles
                if (x * y) % 7 == 0:
                    pygame.draw.circle(surface, stone_dark, 
                                     (x * tile_size + 8, y * tile_size + 8), 2)
            else:
                # Stone layer
                base = stone if (x + y) % 3 == 0 else stone_dark
                pygame.draw.rect(surface, base, rect)
                # Add cracks
                if (x * y) % 11 == 0:
                    pygame.draw.line(surface, stone_dark,
                                   (x * tile_size + 2, y * tile_size + 4),
                                   (x * tile_size + 14, y * tile_size + 12), 1)
    
    pygame.image.save(surface, 'assets/tileset_main.png')
    print("Created tileset_main.png")

if __name__ == '__main__':
    create_player_sprite()
    create_slime_sprite()
    create_fly_sprite()
    create_particles()
    create_tileset()
    print("\n✅ Created all sprite files!")
