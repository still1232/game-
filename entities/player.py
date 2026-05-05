"""
Player entity with movement, jetpack, and combat capabilities
"""
import pygame
from settings import (
    PLAYER_SPEED, PLAYER_JUMP, PLAYER_JETPACK_FORCE, PLAYER_MAX_HP,
    TILE_SIZE, FIRE, SMOKE
)


class Player:
    """Player entity với đầy đủ controls và physics"""
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.width = 3  # tiles
        self.height = 5  # tiles
        self.color = (100, 150, 255)
        
        # Stats
        self.hp = PLAYER_MAX_HP
        self.max_hp = PLAYER_MAX_HP
        self.jetpack_fuel = 100
        self.max_fuel = 100
        
        # State
        self.on_ground = False
        self.is_flying = False
        self.facing_right = True
        self.visible = True
        self.invincible = False
        self.invincible_timer = 0
        
        # Combat
        self.selected_material = FIRE
        self.shoot_cooldown = 0
        self.max_shoot_cooldown = 15
        
        # Animation
        self.anim_frame = 0
        self.anim_timer = 0
        
        # Sprite frames (loaded from sprite sheet)
        self.sprites = []
        self.load_sprites()
        
    def load_sprites(self):
        """Load player sprites from external sprite sheet (Noita-like style)"""
        import os
        asset_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'player_sprites.png')
        try:
            sprite_sheet = pygame.image.load(asset_path).convert_alpha()
            # Extract frames from sprite sheet (assuming 16x16 pixel frames)
            frame_width = 16
            frame_height = 16
            cols = sprite_sheet.get_width() // frame_width
            
            # Get multiple animation frames
            for i in range(min(8, cols)):  # Load up to 8 frames
                frame = sprite_sheet.subsurface(i * frame_width, 0, frame_width, frame_height)
                # Scale to player size
                frame = pygame.transform.scale(frame, (self.width * TILE_SIZE, self.height * TILE_SIZE))
                self.sprites.append(frame)
        except Exception as e:
            print(f"Warning: Could not load player sprite sheet: {e}")
            # Create fallback sprite
            self._create_fallback_sprite()
            
    def _create_fallback_sprite(self):
        """Create simple fallback sprite if external file fails"""
        sprite = pygame.Surface((self.width * TILE_SIZE, self.height * TILE_SIZE), pygame.SRCALPHA)
        pygame.draw.rect(sprite, (100, 150, 255), 
                        (TILE_SIZE, TILE_SIZE, self.width * TILE_SIZE - 2, self.height * TILE_SIZE - 2))
        pygame.draw.circle(sprite, (255, 255, 255), 
                          (int(self.width * TILE_SIZE * 0.7), int(self.height * TILE_SIZE * 0.3)), 4)
        self.sprites.append(sprite)
        
    def get_sprite(self):
        """Get current sprite with animation support"""
        if not self.sprites:
            return None
            
        # Get current animation frame
        current_sprite = self.sprites[self.anim_frame % len(self.sprites)]
        
        if not self.facing_right:
            # Flip sprite if facing left
            return pygame.transform.flip(current_sprite, True, False)
        return current_sprite
        
    def get_rect(self):
        """Get collision rectangle"""
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)
        
    def handle_input(self, keys):
        """Handle player input"""
        self.vx = 0
        
        # Horizontal movement
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.vx = -PLAYER_SPEED
            self.facing_right = False
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.vx = PLAYER_SPEED
            self.facing_right = True
            
        # Jump
        if (keys[pygame.K_w] or keys[pygame.K_SPACE]) and self.on_ground:
            self.vy = PLAYER_JUMP
            self.on_ground = False
            
        # Jetpack
        if keys[pygame.K_LSHIFT] and self.jetpack_fuel > 0:
            self.vy = PLAYER_JETPACK_FORCE
            self.is_flying = True
            self.jetpack_fuel -= 2
            self.on_ground = False
        else:
            self.is_flying = False
            # Regenerate fuel slowly
            if self.jetpack_fuel < self.max_fuel:
                self.jetpack_fuel += 0.5
                
        # Shoot - handled in game loop with mouse
        # Change material
        if keys[pygame.K_1]:
            self.selected_material = FIRE
        elif keys[pygame.K_2]:
            self.selected_material = SMOKE
            
    def update(self, world, dt=1):
        """Update player physics and collision"""
        # Apply gravity
        if not self.is_flying:
            self.vy += 0.5 * dt
        else:
            self.vy *= 0.9  # Air resistance when flying
            
        # Apply velocity
        self.x += self.vx * dt
        self.y += self.vy * dt
        
        # Collision detection with world
        self.check_collision(world)
        
        # Cooldowns
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
            
        if self.invincible_timer > 0:
            self.invincible_timer -= 1
            if self.invincible_timer <= 0:
                self.invincible = False
                
        # Animation
        self.anim_timer += 1
        if self.anim_timer >= 10:
            self.anim_timer = 0
            self.anim_frame = (self.anim_frame + 1) % 4
            
        # Bounds checking
        self.x = max(0, min(self.x, world.width - self.width))
        self.y = max(0, min(self.y, world.height - self.height))
        
    def check_collision(self, world):
        """Simple AABB collision with world pixels"""
        # Check corners of player bounding box
        check_points = [
            (self.x, self.y),
            (self.x + self.width - 1, self.y),
            (self.x, self.y + self.height - 1),
            (self.x + self.width - 1, self.y + self.height - 1),
        ]
        
        for px, py in check_points:
            mat = world.get_pixel(int(px), int(py))
            if mat != 0:  # Not air
                # Simple resolution - push back
                if self.vy > 0:  # Falling
                    self.y = int(py) - self.height
                    self.vy = 0
                    self.on_ground = True
                elif self.vy < 0:  # Jumping up
                    self.y = int(py) + 1
                    self.vy = 0
                    
        # Horizontal collision
        if self.vx != 0:
            front_x = int(self.x + self.width) if self.vx > 0 else int(self.x)
            for y_off in range(self.height):
                mat = world.get_pixel(front_x, int(self.y + y_off))
                if mat != 0:
                    if self.vx > 0:
                        self.x = front_x - self.width
                    else:
                        self.x = front_x + 1
                    self.vx = 0
                    break
                    
    def shoot(self, world, renderer):
        """Shoot projectile/spawn material"""
        if self.shoot_cooldown > 0:
            return False
            
        # Spawn material in front of player
        start_x = int(self.x + self.width // 2)
        start_y = int(self.y + self.height // 2)
        
        direction = 1 if self.facing_right else -1
        
        # Create projectile effect
        for i in range(5):
            px = start_x + (direction * i)
            world.set_pixel(px, start_y, self.selected_material)
            
        self.shoot_cooldown = self.max_shoot_cooldown
        
        # Camera shake
        renderer.add_shake(3, 5)
        
        return True
        
    def take_damage(self, amount):
        """Take damage"""
        if self.invincible:
            return
            
        self.hp -= amount
        self.invincible = True
        self.invincible_timer = 30
        
        if self.hp <= 0:
            self.die()
            
    def die(self):
        """Player death"""
        print("Player died!")
        # Respawn logic would go here
        self.hp = self.max_hp
        self.x = 50
        self.y = 50
        self.vy = 0
        
    def render_ui(self, screen):
        """Render player UI (HP bar, fuel)"""
        # HP bar
        hp_width = 200
        hp_height = 20
        hp_x = 20
        hp_y = 20
        
        # Background
        pygame.draw.rect(screen, (50, 50, 50), (hp_x, hp_y, hp_width, hp_height))
        # HP fill
        hp_percent = self.hp / self.max_hp
        hp_color = (255, 0, 0) if hp_percent < 0.3 else (0, 255, 0)
        pygame.draw.rect(screen, hp_color, (hp_x, hp_y, int(hp_width * hp_percent), hp_height))
        # Border
        pygame.draw.rect(screen, (255, 255, 255), (hp_x, hp_y, hp_width, hp_height), 2)
        
        # Fuel bar
        fuel_width = 150
        fuel_height = 15
        fuel_x = 20
        fuel_y = 50
        
        pygame.draw.rect(screen, (50, 50, 50), (fuel_x, fuel_y, fuel_width, fuel_height))
        fuel_percent = self.jetpack_fuel / self.max_fuel
        pygame.draw.rect(screen, (100, 200, 255), (fuel_x, fuel_y, int(fuel_width * fuel_percent), fuel_height))
        pygame.draw.rect(screen, (255, 255, 255), (fuel_x, fuel_y, fuel_width, fuel_height), 2)
        
        # Selected material indicator
        font = pygame.font.Font(None, 24)
        text = font.render(f"Material: {self.selected_material}", True, (255, 255, 255))
        screen.blit(text, (20, 80))
